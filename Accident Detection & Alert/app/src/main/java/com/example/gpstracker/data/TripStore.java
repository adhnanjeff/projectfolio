package com.example.gpstracker.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Aggregated driving statistics plus a bounded recent-activity timeline.
 *
 * <p>Everything the analytics screen shows comes from here; previously those numbers were
 * hard-coded placeholders that never changed.
 */
public class TripStore {

    private static final String PREFS = "SafeDrivePrefs";
    private static final String KEY_TRIPS = "total_trips";
    private static final String KEY_DISTANCE = "total_distance_km";
    private static final String KEY_MAX_SPEED = "max_speed";
    private static final String KEY_SPEED_SUM = "speed_sum";
    private static final String KEY_SPEED_SAMPLES = "speed_samples";
    private static final String KEY_VIOLATIONS = "violations";
    private static final String KEY_DANGER_ENTRIES = "danger_entries";
    private static final String KEY_EVENTS = "activity_events";

    /** Speed above which a sample counts as a violation, in km/h. */
    public static final float SPEED_LIMIT_KMH = 80f;

    private static final int MAX_EVENTS = 50;

    private final SharedPreferences prefs;

    public TripStore(Context context) {
        this.prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public int getTotalTrips() {
        return prefs.getInt(KEY_TRIPS, 0);
    }

    public float getTotalDistanceKm() {
        return prefs.getFloat(KEY_DISTANCE, 0f);
    }

    public float getMaxSpeed() {
        return prefs.getFloat(KEY_MAX_SPEED, 0f);
    }

    public float getAvgSpeed() {
        int samples = prefs.getInt(KEY_SPEED_SAMPLES, 0);
        if (samples == 0) {
            return 0f;
        }
        return prefs.getFloat(KEY_SPEED_SUM, 0f) / samples;
    }

    public int getViolations() {
        return prefs.getInt(KEY_VIOLATIONS, 0);
    }

    public int getDangerEntries() {
        return prefs.getInt(KEY_DANGER_ENTRIES, 0);
    }

    /**
     * Safety score out of 100: starts at 100 and deducts for speeding and danger-zone entries,
     * scaled by how much driving has actually been recorded so a single early event is not fatal.
     */
    public float getSafetyScore() {
        int trips = getTotalTrips();
        if (trips == 0) {
            return 100f;
        }
        float violationPenalty = Math.min(40f, (getViolations() / (float) trips) * 12f);
        float dangerPenalty = Math.min(30f, (getDangerEntries() / (float) trips) * 6f);
        return Math.max(0f, 100f - violationPenalty - dangerPenalty);
    }

    /** Records one completed trip and folds its stats into the running aggregates. */
    public void recordTrip(float distanceKm, float maxSpeedKmh, float avgSpeedKmh, int violations) {
        SharedPreferences.Editor editor = prefs.edit();
        editor.putInt(KEY_TRIPS, getTotalTrips() + 1);
        editor.putFloat(KEY_DISTANCE, getTotalDistanceKm() + distanceKm);
        editor.putFloat(KEY_MAX_SPEED, Math.max(getMaxSpeed(), maxSpeedKmh));
        editor.putFloat(KEY_SPEED_SUM, prefs.getFloat(KEY_SPEED_SUM, 0f) + avgSpeedKmh);
        editor.putInt(KEY_SPEED_SAMPLES, prefs.getInt(KEY_SPEED_SAMPLES, 0) + 1);
        editor.putInt(KEY_VIOLATIONS, getViolations() + violations);
        editor.apply();
    }

    public void recordDangerEntry() {
        prefs.edit().putInt(KEY_DANGER_ENTRIES, getDangerEntries() + 1).apply();
    }

    public void addEvent(String type, String message) {
        List<ActivityEvent> events = getEvents();
        events.add(0, new ActivityEvent(type, message, System.currentTimeMillis()));
        while (events.size() > MAX_EVENTS) {
            events.remove(events.size() - 1);
        }
        JSONArray array = new JSONArray();
        for (ActivityEvent event : events) {
            try {
                array.put(event.toJson());
            } catch (JSONException ignored) {
                // Skip unserialisable entry.
            }
        }
        prefs.edit().putString(KEY_EVENTS, array.toString()).apply();
    }

    public List<ActivityEvent> getEvents() {
        List<ActivityEvent> events = new ArrayList<>();
        try {
            JSONArray array = new JSONArray(prefs.getString(KEY_EVENTS, "[]"));
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o != null) {
                    events.add(ActivityEvent.fromJson(o));
                }
            }
        } catch (JSONException ignored) {
            // Corrupt payload – return whatever parsed.
        }
        return events;
    }

    public void clear() {
        prefs.edit()
                .remove(KEY_TRIPS)
                .remove(KEY_DISTANCE)
                .remove(KEY_MAX_SPEED)
                .remove(KEY_SPEED_SUM)
                .remove(KEY_SPEED_SAMPLES)
                .remove(KEY_VIOLATIONS)
                .remove(KEY_DANGER_ENTRIES)
                .remove(KEY_EVENTS)
                .apply();
    }
}
