from src.storage.storage_handler import get_worksheet

EXPECTED_HEADERS = ["id", "name", "player", "class", "level", "stats", "inventory"]


def main():
    worksheet = get_worksheet(sheet_name="Characters")  # default tab name; adjust if you renamed it
    header_row = worksheet.row_values(1)
    records = worksheet.get_all_records()

    print(f"Connected to: {worksheet.spreadsheet.title}")
    print(f"Header row: {header_row}")
    print(f"Row count (data only): {len(records)}")

    if header_row != EXPECTED_HEADERS:
        print(f"\nWARNING: headers don't match expected {EXPECTED_HEADERS}")
    else:
        print("\nConnection OK.")


if __name__ == "__main__":
    main()