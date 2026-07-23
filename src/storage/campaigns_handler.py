from src.storage.storage_handler import get_worksheet

def query_campaigns_by_schedule(day=None, preference_tags=None, worksheet=None):
    if worksheet is None:
        worksheet = get_worksheet(sheet_name="Campaigns")

    preference_tags = preference_tags or []
    records = worksheet.get_all_records()

    scored = []
    for record in records:
        if day and record.get("day", "").strip().lower() != day.strip().lower():
            continue

        record_tags = [t.strip().lower() for t in record.get("preference_tags", "").split(",") if t.strip()]
        overlap = len(set(t.lower() for t in preference_tags) & set(record_tags))

        if preference_tags and overlap == 0:
            continue

        enriched = dict(record)
        enriched["incomplete_contact"] = not bool(record.get("contact", "").strip())
        scored.append((enriched, overlap))

    scored.sort(key=lambda pair: pair[1], reverse=True)

    if not scored:
        return {"status": "no_match", "message": "no campaigns found for this schedule/preference"}

    return {"status": "success", "data": {"campaigns": [record for record, _ in scored]}}