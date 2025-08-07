import requests, json, html, re
from bs4 import BeautifulSoup
from .models import Job

def clean_malformed_json(raw):
    raw = html.unescape(raw)

    # Remove trailing commas before } or ]
    raw = re.sub(r",\s*([\]}])", r"\1", raw)

    # Remove newlines and other control characters inside strings
    raw = re.sub(r'[\n\r\t]+', ' ', raw)

    # Replace broken HTML escape sequences that mess up JSON parsing
    raw = raw.replace('</', '<\\/')

    return raw


def scrape_remoteok():
    url = "https://remoteok.com/remote-dev-jobs"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("❌ Failed to fetch page")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    job_elements = soup.select("tr.job")

    for tr in job_elements[:5]:  # Limit to first 5 for testing
        script_tag = tr.find("script", type="application/ld+json")
        if not script_tag:
            continue

        try:
            raw_json = script_tag.string.strip()
            raw_json = clean_malformed_json(raw_json)

            # 🛡 Skip known problematic job (like Melapress)
            if "Melapress" in raw_json or len(raw_json) < 1000:
                print("🚫 Skipping known bad or incomplete job")
                continue

            try:
                data = json.loads(raw_json)
            except json.JSONDecodeError as json_err:
                print(f"❌ JSON decode error: {json_err}")
                print("🔎 Raw JSON snippet:\n", raw_json[:500])
                continue

            title = data.get("title")
            company = data.get("hiringOrganization", {}).get("name")
            description = BeautifulSoup(data.get("description", ""), "html.parser").text.strip()
            location = data.get("jobLocationType", "Remote")
            link = "https://remoteok.com" + tr.get("data-href")

            # Avoid duplicates
            if Job.objects.filter(title=title, company=company, link=link).exists():
                print(f"⚠️ Skipping duplicate: {title}")
                continue

            Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=description,
                link=link,
                source="RemoteOK",
                raw_html=str(tr)
            )
            print(f"💾 Saved: {title}")

        except Exception as e:
            print("❌ Error parsing job:", e)
