package com.example.gpstracker.data;

import org.json.JSONException;
import org.json.JSONObject;

/** A single entry in the recent-activity timeline. */
public class ActivityEvent {

    public static final String TYPE_TRIP = "trip";
    public static final String TYPE_DANGER = "danger";
    public static final String TYPE_VIOLATION = "violation";
    public static final String TYPE_SOS = "sos";

    public final String type;
    public final String message;
    public final long timestamp;

    public ActivityEvent(String type, String message, long timestamp) {
        this.type = type;
        this.message = message;
        this.timestamp = timestamp;
    }

    JSONObject toJson() throws JSONException {
        JSONObject o = new JSONObject();
        o.put("type", type);
        o.put("message", message);
        o.put("ts", timestamp);
        return o;
    }

    static ActivityEvent fromJson(JSONObject o) {
        return new ActivityEvent(o.optString("type"), o.optString("message"), o.optLong("ts"));
    }
}
