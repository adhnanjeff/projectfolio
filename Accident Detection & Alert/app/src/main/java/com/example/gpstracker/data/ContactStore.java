package com.example.gpstracker.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Persists emergency contacts as a JSON array in SharedPreferences. */
public class ContactStore {

    private static final String PREFS = "SafeDrivePrefs";
    private static final String KEY_CONTACTS = "emergency_contacts";

    private final SharedPreferences prefs;

    public ContactStore(Context context) {
        this.prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public List<EmergencyContact> getAll() {
        List<EmergencyContact> contacts = new ArrayList<>();
        try {
            JSONArray array = new JSONArray(prefs.getString(KEY_CONTACTS, "[]"));
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o != null) {
                    contacts.add(EmergencyContact.fromJson(o));
                }
            }
        } catch (JSONException ignored) {
            // Corrupt payload – return whatever parsed.
        }
        return contacts;
    }

    public void add(String name, String phone) {
        List<EmergencyContact> contacts = getAll();
        contacts.add(new EmergencyContact(UUID.randomUUID().toString(), name, phone));
        save(contacts);
    }

    public void remove(String id) {
        List<EmergencyContact> contacts = getAll();
        for (int i = contacts.size() - 1; i >= 0; i--) {
            if (contacts.get(i).id.equals(id)) {
                contacts.remove(i);
            }
        }
        save(contacts);
    }

    private void save(List<EmergencyContact> contacts) {
        JSONArray array = new JSONArray();
        for (EmergencyContact contact : contacts) {
            try {
                array.put(contact.toJson());
            } catch (JSONException ignored) {
                // Skip unserialisable entry rather than dropping the list.
            }
        }
        prefs.edit().putString(KEY_CONTACTS, array.toString()).apply();
    }
}
