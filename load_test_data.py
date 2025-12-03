"""
Script to load test data into the database
"""
import json
from datetime import datetime
from app.data_manager import get_data_manager

def load_test_calls():
    """Load test calls from JSON file"""

    # Read test data
    with open('test_data_for_api/test_calls.json', 'r') as f:
        calls_data = json.load(f)

    manager = get_data_manager()

    print(f"Loading {len(calls_data)} test calls...\n")

    for i, call_data in enumerate(calls_data, 1):
        print(f"{'='*60}")
        print(f"Loading call {i}/{len(calls_data)}")
        print(f"{'='*60}")

        # Generate unique call_id
        call_id = f"test-call-{call_data['date']}-{i}"

        # Parse date
        date = datetime.strptime(call_data['date'], "%Y-%m-%d")

        # Extract metadata
        meta = call_data.get('meta-data', {})
        meeting_type = meta.get('call_type', 'general')
        duration = meta.get('duration_minutes', 30)

        try:
            result = manager.add_call(
                call_id=call_id,
                full_transcript=call_data['transcript'],
                summary=call_data['summary'],
                date=date,
                attendants=call_data['attendants'],
                topic=f"Meeting on {call_data['date']}",
                meeting_type=meeting_type,
                duration_minutes=duration,
                meta=meta
            )

            print(f"✅ Successfully loaded: {call_id}")
            print(f"   Chunks: {result['chunks_count']}")
            print(f"   Attendants: {', '.join(call_data['attendants'])}")
            print()

        except Exception as e:
            print(f"❌ Failed to load {call_id}: {str(e)}")
            print()

    print(f"{'='*60}")
    print("✨ All test data loaded!")
    print(f"{'='*60}")

if __name__ == "__main__":
    load_test_calls()