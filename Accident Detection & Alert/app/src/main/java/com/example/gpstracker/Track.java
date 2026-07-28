package com.example.gpstracker;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.os.Build;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;

import com.example.gpstracker.data.ActivityEvent;
import com.example.gpstracker.data.DangerZone;
import com.example.gpstracker.data.DangerZoneStore;
import com.example.gpstracker.data.TripStore;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationCallback;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.Priority;

import java.util.List;
import java.util.Locale;

/**
 * Foreground service that watches the user's location, measures the distance to the nearest
 * danger zone, and records trip statistics.
 */
public class Track extends Service {

    public static final String ACTION_UPDATE = "com.example.gpstracker.LOCATION_UPDATE";
    public static final String EXTRA_CLOSEST_KM = "closest";
    public static final String EXTRA_ZONE_NAME = "zone_name";
    public static final String EXTRA_SPEED_KMH = "speed";
    public static final String EXTRA_LATITUDE = "latitude";
    public static final String EXTRA_LONGITUDE = "longitude";
    public static final String EXTRA_HAS_ZONES = "has_zones";

    /** Radius, in km, within which a location counts as inside a danger zone. */
    public static final double DANGER_RADIUS_KM = 1.5;

    private static final String CHANNEL_ID = "safedrive_tracking";
    private static final int NOTIFICATION_ID = 1001;
    private static final long UPDATE_INTERVAL_MS = 5000L;

    private static final float TRIP_START_SPEED_KMH = 10f;
    private static final float TRIP_IDLE_SPEED_KMH = 3f;
    private static final long TRIP_IDLE_TIMEOUT_MS = 120_000L;

    private FusedLocationProviderClient fusedLocationProviderClient;
    private LocationCallback locationCallback;
    private DangerZoneStore zoneStore;
    private TripStore tripStore;

    // Active-trip accumulators.
    private boolean tripActive = false;
    private float tripDistanceKm = 0f;
    private float tripMaxSpeed = 0f;
    private float tripSpeedSum = 0f;
    private int tripSpeedSamples = 0;
    private int tripViolations = 0;
    private boolean overSpeedLimit = false;
    private long idleSinceMs = 0L;
    private Location lastLocation;
    private boolean insideDangerZone = false;

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        zoneStore = new DangerZoneStore(this);
        tripStore = new TripStore(this);
        fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this);

        locationCallback = new LocationCallback() {
            @Override
            public void onLocationResult(@NonNull LocationResult locationResult) {
                Location location = locationResult.getLastLocation();
                if (location == null) {
                    return;
                }
                handleLocation(location);
            }
        };
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startInForeground();
        requestLocation();
        // Restart if the system kills us – this is a safety feature.
        return START_STICKY;
    }

    private void startInForeground() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && manager != null) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Trip tracking", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Keeps SafeDrive monitoring your location while driving.");
            manager.createNotificationChannel(channel);
        }

        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            flags |= PendingIntent.FLAG_IMMUTABLE;
        }
        PendingIntent contentIntent = PendingIntent.getActivity(
                this, 0, new Intent(this, MainActivity.class), flags);

        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle(getString(R.string.app_name))
                .setContentText("Monitoring for accident-prone areas")
                .setSmallIcon(R.mipmap.ic_launcher)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .setOngoing(true)
                .setContentIntent(contentIntent)
                .build();

        // startForeground must run on every API level, not only on O+, or the service is
        // treated as a background service and killed on modern Android.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification,
                    android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    private void requestLocation() {
        if (!hasLocationPermission()) {
            stopSelf();
            return;
        }
        LocationRequest locationRequest = new LocationRequest.Builder(
                Priority.PRIORITY_HIGH_ACCURACY, UPDATE_INTERVAL_MS)
                .setMinUpdateIntervalMillis(UPDATE_INTERVAL_MS)
                .build();
        fusedLocationProviderClient.requestLocationUpdates(
                locationRequest, locationCallback, Looper.getMainLooper());
    }

    private boolean hasLocationPermission() {
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
                || ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    private void handleLocation(Location location) {
        float speedKmh = location.getSpeed() * 3.6f;
        updateTrip(location, speedKmh);
        broadcastDanger(location, speedKmh);
        lastLocation = location;
    }

    /** Starts, accumulates, and ends trips based on movement. */
    private void updateTrip(Location location, float speedKmh) {
        long now = System.currentTimeMillis();

        if (!tripActive) {
            if (speedKmh >= TRIP_START_SPEED_KMH) {
                tripActive = true;
                tripDistanceKm = 0f;
                tripMaxSpeed = 0f;
                tripSpeedSum = 0f;
                tripSpeedSamples = 0;
                tripViolations = 0;
                overSpeedLimit = false;
                idleSinceMs = 0L;
            } else {
                return;
            }
        }

        if (lastLocation != null) {
            tripDistanceKm += location.distanceTo(lastLocation) / 1000f;
        }
        tripMaxSpeed = Math.max(tripMaxSpeed, speedKmh);
        tripSpeedSum += speedKmh;
        tripSpeedSamples++;

        // Count one violation per crossing of the limit, not one per sample.
        if (speedKmh > TripStore.SPEED_LIMIT_KMH) {
            if (!overSpeedLimit) {
                overSpeedLimit = true;
                tripViolations++;
                tripStore.addEvent(ActivityEvent.TYPE_VIOLATION,
                        String.format(Locale.getDefault(), "Speed limit exceeded – %.0f km/h", speedKmh));
            }
        } else {
            overSpeedLimit = false;
        }

        if (speedKmh < TRIP_IDLE_SPEED_KMH) {
            if (idleSinceMs == 0L) {
                idleSinceMs = now;
            } else if (now - idleSinceMs >= TRIP_IDLE_TIMEOUT_MS) {
                endTrip();
            }
        } else {
            idleSinceMs = 0L;
        }
    }

    private void endTrip() {
        if (!tripActive) {
            return;
        }
        float avgSpeed = tripSpeedSamples == 0 ? 0f : tripSpeedSum / tripSpeedSamples;
        tripStore.recordTrip(tripDistanceKm, tripMaxSpeed, avgSpeed, tripViolations);
        tripStore.addEvent(ActivityEvent.TYPE_TRIP,
                String.format(Locale.getDefault(), "Trip completed – %.1f km, max %.0f km/h",
                        tripDistanceKm, tripMaxSpeed));
        tripActive = false;
        idleSinceMs = 0L;
    }

    private void broadcastDanger(Location location, float speedKmh) {
        List<DangerZone> zones = zoneStore.getAll();

        Intent intent = new Intent(ACTION_UPDATE);
        intent.setPackage(getPackageName());
        intent.putExtra(EXTRA_SPEED_KMH, speedKmh);
        intent.putExtra(EXTRA_LATITUDE, location.getLatitude());
        intent.putExtra(EXTRA_LONGITUDE, location.getLongitude());
        intent.putExtra(EXTRA_HAS_ZONES, !zones.isEmpty());

        if (zones.isEmpty()) {
            insideDangerZone = false;
            sendBroadcast(intent);
            return;
        }

        double closest = Double.MAX_VALUE;
        String closestName = "";
        for (DangerZone zone : zones) {
            double distance = getDistance(
                    location.getLatitude(), location.getLongitude(), zone.latitude, zone.longitude);
            if (distance < closest) {
                closest = distance;
                closestName = zone.name;
            }
        }

        // Log a danger-zone entry once per entry rather than on every fix inside the zone.
        if (closest <= DANGER_RADIUS_KM) {
            if (!insideDangerZone) {
                insideDangerZone = true;
                tripStore.recordDangerEntry();
                tripStore.addEvent(ActivityEvent.TYPE_DANGER, "Entered danger zone – " + closestName);
            }
        } else {
            insideDangerZone = false;
        }

        intent.putExtra(EXTRA_CLOSEST_KM, closest);
        intent.putExtra(EXTRA_ZONE_NAME, closestName);
        sendBroadcast(intent);
    }

    /** Great-circle distance in kilometres (haversine). */
    private double getDistance(double lat1, double lon1, double lat2, double lon2) {
        final int earthRadiusKm = 6371;
        double dLat = deg2rad(lat2 - lat1);
        double dLon = deg2rad(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                + Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2))
                * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return earthRadiusKm * c;
    }

    private double deg2rad(double deg) {
        return deg * (Math.PI / 180);
    }

    @Override
    public void onDestroy() {
        // Persist an in-flight trip instead of silently discarding it.
        endTrip();
        if (fusedLocationProviderClient != null && locationCallback != null) {
            fusedLocationProviderClient.removeLocationUpdates(locationCallback);
        }
        Log.d("Track", "Tracking service stopped");
        super.onDestroy();
    }
}
