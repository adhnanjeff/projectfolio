package com.example.gpstracker.data;

import org.json.JSONException;
import org.json.JSONObject;

/** A person notified when the user triggers SOS. */
public class EmergencyContact {

    public final String id;
    public final String name;
    public final String phone;

    public EmergencyContact(String id, String name, String phone) {
        this.id = id;
        this.name = name;
        this.phone = phone;
    }

    JSONObject toJson() throws JSONException {
        JSONObject o = new JSONObject();
        o.put("id", id);
        o.put("name", name);
        o.put("phone", phone);
        return o;
    }

    static EmergencyContact fromJson(JSONObject o) {
        return new EmergencyContact(o.optString("id"), o.optString("name"), o.optString("phone"));
    }
}
