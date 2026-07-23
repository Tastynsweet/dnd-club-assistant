from src.storage.campaigns_handler import query_campaigns_by_schedule

class FakeWorksheet:
    def __init__(self, records=None):
        self._records = records or []

    def get_all_records(self):
        return self._records

CAMPAIGNS = [
    {
        "campaign_id": "camp_012",
        "name": "Lost Mine of Phandelver",
        "day": "Saturday",
        "level_range": "1-5",
        "preference_tags": "low-level, one-shot",
        "contact": "dm1@example.com",
    },
    {
        "campaign_id": "camp_019",
        "name": "Curse of Strahd",
        "day": "Saturday",
        "level_range": "5-10",
        "preference_tags": "horror, campaign",
        "contact": "",
    },
    {
        "campaign_id": "camp_020",
        "name": "Tuesday Night One-Shots",
        "day": "Tuesday",
        "level_range": "1-3",
        "preference_tags": "low-level, one-shot",
        "contact": "dm2@example.com",
    },
]

def test_query_matches_day_and_ranks_by_tag_overlap():
    ws = FakeWorksheet(CAMPAIGNS)
    result = query_campaigns_by_schedule(day="Saturday", preference_tags=["low-level", "one-shot"], worksheet=ws)

    assert result["status"] == "success"
    campaigns = result["data"]["campaigns"]
    assert campaigns[0]["campaign_id"] == "camp_012"

def test_query_flags_incomplete_contact():
    ws = FakeWorksheet(CAMPAIGNS)
    result = query_campaigns_by_schedule(day="Saturday", preference_tags=["horror"], worksheet=ws)

    campaigns = result["data"]["campaigns"]
    assert campaigns[0]["campaign_id"] == "camp_019"
    assert campaigns[0]["incomplete_contact"] is True

def test_query_no_match_returns_no_match_status():
    ws = FakeWorksheet(CAMPAIGNS)
    result = query_campaigns_by_schedule(day="Sunday", preference_tags=["horror"], worksheet=ws)

    assert result["status"] == "no_match"

def test_query_by_day_only_ignores_preference_filter():
    ws = FakeWorksheet(CAMPAIGNS)
    result = query_campaigns_by_schedule(day="Saturday", worksheet=ws)

    assert result["status"] == "success"
    assert len(result["data"]["campaigns"]) == 2