package com.example.gpstracker.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Persists user-managed danger zones as a JSON array in SharedPreferences.
 *
 * <p>Replaces the old {@code HashMap<lat, lon>} in the tracking service, which silently
 * dropped zones that happened to share a latitude.
 */
public class DangerZoneStore {

    private static final String PREFS = "SafeDrivePrefs";
    private static final String KEY_ZONES = "danger_zones";
    private static final String KEY_SEEDED = "danger_zones_seeded";

    private final SharedPreferences prefs;

    public DangerZoneStore(Context context) {
        this.prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        seedDefaultsOnce();
    }

    /** Ships a few sample zones on first launch so the app is not silent out of the box. */
    private void seedDefaultsOnce() {
        if (prefs.getBoolean(KEY_SEEDED, false)) {
            return;
        }
        List<DangerZone> defaults = new ArrayList<>();
        defaults.add(new DangerZone(UUID.randomUUID().toString(), "Sample zone – Coimbatore", 10.9760560, 76.9667759));
        defaults.add(new DangerZone(UUID.randomUUID().toString(), "Sample zone – Stone Bench", 11.101138, 76.965810));
        save(defaults);
        prefs.edit().putBoolean(KEY_SEEDED, true).apply();
    }

    public List<DangerZone> getAll() {
        List<DangerZone> zones = new ArrayList<>();
        String raw = prefs.getString(KEY_ZONES, "[]");
        try {
            JSONArray array = new JSONArray(raw);
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o != null) {
                    zones.add(DangerZone.fromJson(o));
                }
            }
        } catch (JSONException ignored) {
            // Corrupt payload – fall through and return whatever parsed.
        }
        return zones;
    }

    public void add(String name, double latitude, double longitude) {
        List<DangerZone> zones = getAll();
        zones.add(new DangerZone(UUID.randomUUID().toString(), name, latitude, longitude));
        save(zones);
    }

    public void remove(String id) {
        List<DangerZone> zones = getAll();
        for (int i = zones.size() - 1; i >= 0; i--) {
            if (zones.get(i).id.equals(id)) {
                zones.remove(i);
            }
        }
        save(zones);
    }

    private void save(List<DangerZone> zones) {
        JSONArray array = new JSONArray();
        for (DangerZone zone : zones) {
            try {
                array.put(zone.toJson());
            } catch (JSONException ignored) {
                // Skip a zone we cannot serialise rather than losing the whole list.
            }
        }
        prefs.edit().putString(KEY_ZONES, array.toString()).apply();
    }
}
