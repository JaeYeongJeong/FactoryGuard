from app.db.mongodb import db

# Collections
event_collection = db["events"]
camera_capture_collection = db["camera_captures"]
incident_report_collection = db["incident_reports"]


def create_indexes():
    # ===== events =====
    event_collection.create_index("event_id", unique=True)
    event_collection.create_index("event_type")
    event_collection.create_index("camera_id")
    event_collection.create_index("timestamp")
    event_collection.create_index("confidence")
    event_collection.create_index("status")

    # ===== camera_captures =====
    camera_capture_collection.create_index("capture_id", unique=True)
    camera_capture_collection.create_index("event_id")
    camera_capture_collection.create_index("image_path")
    camera_capture_collection.create_index("created_at")
    

    # ===== incident_reports =====
    incident_report_collection.create_index("incident_id", unique=True)
    incident_report_collection.create_index("event_id")
    incident_report_collection.create_index("created_at")