package com.example.gpstracker.data;

import org.json.JSONException;
import org.json.JSONObject;

/** A user-defined accident-prone area. */
public class DangerZone {

    public final String id;
    public final String name;
    public final double latitude;
    public final double longitude;

    public DangerZone(String id, String name, double latitude, double longitude) {
        this.id = id;
        this.name = name;
        this.latitude = latitude;
        this.longitude = longitude;
    }

    JSONObject toJson() throws JSONException {
        JSONObject o = new JSONObject();
        o.put("id", id);
        o.put("name", name);
        o.put("lat", latitude);
        o.put("lon", longitude);
        return o;
    }

    static DangerZone fromJson(JSONObject o) {
        return new DangerZone(
                o.optString("id"),
                o.optString("name"),
                o.optDouble("lat", 0),
                o.optDouble("lon", 0));
    }
}
