package com.example.gpstracker;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.app.admin.DevicePolicyManager;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import com.example.gpstracker.data.ActivityEvent;
import com.example.gpstracker.data.TripStore;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

import java.io.IOException;
import java.text.DecimalFormat;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity implements TextToSpeech.OnInitListener {

    public static final int LOCATION_PERMISSION_REQUEST_CODE = 44;
    public static final int SMS_PERMISSION_REQUEST_CODE = 45;
    public static final int NOTIFICATION_PERMISSION_REQUEST_CODE = 46;

    private static final DecimalFormat df = new DecimalFormat("0.00");
    private static final DecimalFormat speedFormat = new DecimalFormat("0");

    /** Distance below which the status turns amber, in km. */
    private static final double CAUTION_RADIUS_KM = 3.0;
    /** Minimum gap between spoken/audible danger alerts. */
    private static final long ALERT_COOLDOWN_MS = 60_000L;
    /** Minimum gap between reverse-geocode lookups. */
    private static final long GEOCODE_INTERVAL_MS = 30_000L;

    private LocationManager locationManager;
    private MaterialButton b_enable, b_maps, btn_emergency, btn_zones, btn_history, btn_contacts, btn_analytics;
    private TextView lat, lon, dist, add, status_text, speed;
    private View status_indicator, status_banner;
    private int currentBannerRes = 0;

    private FusedLocationProviderClient fusedLocationProviderClient;
    private DevicePolicyManager devicePolicyManager;
    private ComponentName componentName;
    private TextToSpeech textToSpeech;
    private boolean ttsReady = false;
    private Vibrator vibrator;
    private TripStore tripStore;

    private MediaPlayer alertPlayer;
    private long lastAlertMs = 0L;
    private boolean insideDangerZone = false;
    private boolean lockScheduled = false;
    private boolean receiverRegistered = false;

    private double currentLatitude = 0;
    private double currentLongitude = 0;
    private boolean hasFix = false;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final ExecutorService geocoderExecutor = Executors.newSingleThreadExecutor();
    private long lastGeocodeMs = 0L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();

        tripStore = new TripStore(this);
        devicePolicyManager = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        componentName = new ComponentName(this, Controller.class);
        fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this);
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        textToSpeech = new TextToSpeech(this, this);

        setupClickListeners();
        updateDrivingModeLabel();
        requestNotificationPermissionIfNeeded();
        checkLocationPermission();
    }

    private void initViews() {
        b_enable = findViewById(R.id.b_enable);
        b_maps = findViewById(R.id.maps);
        btn_emergency = findViewById(R.id.btn_emergency);
        btn_zones = findViewById(R.id.btn_zones);
        btn_history = findViewById(R.id.btn_history);
        btn_contacts = findViewById(R.id.btn_contacts);
        btn_analytics = findViewById(R.id.btn_analytics);

        lat = findViewById(R.id.lat);
        lon = findViewById(R.id.lon);
        dist = findViewById(R.id.distance);
        add = findViewById(R.id.add);
        speed = findViewById(R.id.speed);
        status_text = findViewById(R.id.status_text);
        status_indicator = findViewById(R.id.status_indicator);
        status_banner = findViewById(R.id.status_banner);
    }

    private void setupClickListeners() {
        b_enable.setOnClickListener(v -> toggleDrivingMode());

        b_maps.setOnClickListener(v -> openMaps());

        btn_emergency.setOnClickListener(v -> confirmSos());

        btn_zones.setOnClickListener(v ->
                startActivity(new Intent(this, DangerZonesActivity.class)));

        btn_contacts.setOnClickListener(v ->
                startActivity(new Intent(this, EmergencyContactsActivity.class)));

        // History and Analytics both open the analytics screen, which owns the timeline.
        btn_analytics.setOnClickListener(v ->
                startActivity(new Intent(this, AnalyticsActivity.class)));
        btn_history.setOnClickListener(v ->
                startActivity(new Intent(this, AnalyticsActivity.class)));
    }

    private void toggleDrivingMode() {
        if (devicePolicyManager.isAdminActive(componentName)) {
            devicePolicyManager.removeActiveAdmin(componentName);
            updateDrivingModeLabel();
        } else {
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, componentName);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, getString(R.string.app_description));
            startActivity(intent);
            // The label is refreshed in onResume once we know whether the user accepted.
        }
    }

    /** Reflects the real admin state instead of optimistically flipping the label. */
    private void updateDrivingModeLabel() {
        boolean active = devicePolicyManager.isAdminActive(componentName);
        b_enable.setText(active ? R.string.disable_driving_mode : R.string.enable_driving_mode);
    }

    private void openMaps() {
        if (!hasFix) {
            Snackbar.make(b_maps, R.string.sos_no_location, Snackbar.LENGTH_SHORT).show();
            return;
        }
        // Build the URI from the raw coordinates – the TextViews contain display labels.
        String geoUri = String.format(Locale.US, "geo:%f,%f?q=%f,%f(Your Location)",
                currentLatitude, currentLongitude, currentLatitude, currentLongitude);
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(geoUri));
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivity(intent);
        } else {
            Snackbar.make(b_maps, "No maps app installed", Snackbar.LENGTH_SHORT).show();
        }
    }

    private void confirmSos() {
        new AlertDialog.Builder(this)
                .setTitle(R.string.sos_confirm_title)
                .setMessage(R.string.sos_confirm_message)
                .setPositiveButton(R.string.sos_send, (dialog, which) -> triggerSos())
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }

    private void triggerSos() {
        if (!hasFix) {
            Snackbar.make(btn_emergency, R.string.sos_no_location, Snackbar.LENGTH_LONG).show();
            return;
        }
        vibrate(500);
        int sent = SosHelper.sendSos(this, currentLatitude, currentLongitude);
        if (sent > 0) {
            speak("Emergency alert sent");
            Snackbar.make(btn_emergency, getString(R.string.sos_sent, sent), Snackbar.LENGTH_LONG).show();
        }
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.POST_NOTIFICATIONS},
                    NOTIFICATION_PERMISSION_REQUEST_CODE);
        }
    }

    private void checkLocationPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION},
                    LOCATION_PERMISSION_REQUEST_CODE);
        } else {
            onLocationPermissionGranted();
        }
    }

    /** The tracking service is only started once permission actually exists. */
    private void onLocationPermissionGranted() {
        startTrackingService();
        promptForLocationServicesIfDisabled();
        resolveAddress();
    }

    private void startTrackingService() {
        Intent serviceIntent = new Intent(this, Track.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                onLocationPermissionGranted();
            } else {
                Snackbar.make(b_enable, "Location permission is required to detect danger zones",
                        Snackbar.LENGTH_LONG).show();
            }
        } else if (requestCode == SMS_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                triggerSos();
            } else {
                Snackbar.make(btn_emergency, "SMS permission is required to send SOS alerts",
                        Snackbar.LENGTH_LONG).show();
            }
        }
    }

    private void promptForLocationServicesIfDisabled() {
        if (locationManager == null || locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle("Enable Location")
                .setMessage("Location is disabled. Enable it in settings?")
                .setPositiveButton("Yes", (dialog, which) ->
                        startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)))
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }

    /** One-shot reverse geocode for the address card; live updates arrive from the service. */
    private void resolveAddress() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        fusedLocationProviderClient.getLastLocation().addOnSuccessListener(this, location -> {
            if (location == null) {
                return;
            }
            updateCoordinates(location.getLatitude(), location.getLongitude());
            updateAddress(location.getLatitude(), location.getLongitude());
        });
    }

    /**
     * Reverse-geocodes off the main thread. {@link Geocoder#getFromLocation} performs blocking
     * network I/O, so calling it inline would risk an ANR.
     */
    private void updateAddress(double latitude, double longitude) {
        geocoderExecutor.execute(() -> {
            String line = null;
            try {
                Geocoder geocoder = new Geocoder(this, Locale.getDefault());
                List<Address> addresses = geocoder.getFromLocation(latitude, longitude, 1);
                if (addresses != null && !addresses.isEmpty()) {
                    line = addresses.get(0).getAddressLine(0);
                }
            } catch (IOException e) {
                Log.w("MainActivity", "Reverse geocoding failed", e);
            }
            // Fall back to raw coordinates so the card never sticks on "Fetching location…".
            final String resolved = line != null ? line
                    : String.format(Locale.US, "%.5f, %.5f", latitude, longitude);
            mainHandler.post(() -> add.setText(resolved));
        });
    }

    /** Re-resolves the address only occasionally – geocoding is a network round trip. */
    private void maybeRefreshAddress(double latitude, double longitude) {
        long now = System.currentTimeMillis();
        if (now - lastGeocodeMs < GEOCODE_INTERVAL_MS) {
            return;
        }
        lastGeocodeMs = now;
        updateAddress(latitude, longitude);
    }

    private void updateCoordinates(double latitude, double longitude) {
        currentLatitude = latitude;
        currentLongitude = longitude;
        hasFix = true;
        lat.setText(df.format(latitude));
        lon.setText(df.format(longitude));
    }

    private final BroadcastReceiver broadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            updateCoordinates(
                    intent.getDoubleExtra(Track.EXTRA_LATITUDE, currentLatitude),
                    intent.getDoubleExtra(Track.EXTRA_LONGITUDE, currentLongitude));
            maybeRefreshAddress(currentLatitude, currentLongitude);

            float speedKmh = intent.getFloatExtra(Track.EXTRA_SPEED_KMH, 0f);
            speed.setText(speedFormat.format(speedKmh) + " km/h");

            if (!intent.getBooleanExtra(Track.EXTRA_HAS_ZONES, false)) {
                dist.setText(R.string.placeholder_dash);
                setStatus(R.string.status_safe, R.drawable.bg_status_safe);
                insideDangerZone = false;
                return;
            }

            double closest = intent.getDoubleExtra(Track.EXTRA_CLOSEST_KM, Double.MAX_VALUE);
            String zoneName = intent.getStringExtra(Track.EXTRA_ZONE_NAME);
            updateDistanceLabel(closest);
            handleProximity(closest, zoneName);
        }
    };

    private void updateDistanceLabel(double closestKm) {
        if (closestKm < 1) {
            dist.setText(df.format(closestKm * 1000) + " m");
        } else {
            dist.setText(df.format(closestKm) + " km");
        }
    }

    private void handleProximity(double closestKm, String zoneName) {
        if (closestKm <= Track.DANGER_RADIUS_KM) {
            setStatus(R.string.status_danger, R.drawable.bg_status_danger);
            if (!insideDangerZone) {
                insideDangerZone = true;
                onEnterDangerZone(zoneName);
            }
        } else {
            insideDangerZone = false;
            lockScheduled = false;
            if (closestKm <= CAUTION_RADIUS_KM) {
                setStatus(R.string.status_caution, R.drawable.bg_status_caution);
            } else {
                setStatus(R.string.status_safe, R.drawable.bg_status_safe);
            }
        }
    }

    private void onEnterDangerZone(String zoneName) {
        long now = System.currentTimeMillis();
        if (now - lastAlertMs >= ALERT_COOLDOWN_MS) {
            lastAlertMs = now;
            playAlertSound();
            vibrate(800);
            speak("Caution. You are entering an accident prone area. "
                    + (zoneName == null ? "" : zoneName));
        }
        scheduleScreenLock();
    }

    private void scheduleScreenLock() {
        if (lockScheduled || !devicePolicyManager.isAdminActive(componentName)) {
            return;
        }
        lockScheduled = true;
        Toast.makeText(this,
                "Entering accident-prone zone. Screen will lock unless driving mode is disabled.",
                Toast.LENGTH_LONG).show();
        mainHandler.postDelayed(() -> {
            if (devicePolicyManager.isAdminActive(componentName) && insideDangerZone) {
                try {
                    devicePolicyManager.lockNow();
                    tripStore.addEvent(ActivityEvent.TYPE_DANGER, "Screen locked in danger zone");
                } catch (SecurityException e) {
                    Log.e("MainActivity", "Unable to lock screen", e);
                }
            }
        }, 10_000L);
    }

    /** Recolours the whole status banner so the state is readable at a glance while driving. */
    private void setStatus(int textRes, int bannerRes) {
        status_text.setText(textRes);
        if (currentBannerRes != bannerRes) {
            currentBannerRes = bannerRes;
            status_banner.setBackgroundResource(bannerRes);
        }
    }

    /** Releases the previous player before starting a new one so instances do not leak. */
    private void playAlertSound() {
        releaseAlertPlayer();
        alertPlayer = MediaPlayer.create(this, R.raw.accident);
        if (alertPlayer == null) {
            return;
        }
        alertPlayer.setOnCompletionListener(mp -> releaseAlertPlayer());
        alertPlayer.start();
    }

    private void releaseAlertPlayer() {
        if (alertPlayer != null) {
            alertPlayer.release();
            alertPlayer = null;
        }
    }

    private void speak(String text) {
        if (ttsReady && textToSpeech != null) {
            textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, "safedrive");
        }
    }

    private void vibrate(long milliseconds) {
        if (vibrator == null || !vibrator.hasVibrator()) {
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(
                    milliseconds, VibrationEffect.DEFAULT_AMPLITUDE));
        } else {
            //noinspection deprecation
            vibrator.vibrate(milliseconds);
        }
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            int result = textToSpeech.setLanguage(Locale.US);
            ttsReady = result != TextToSpeech.LANG_MISSING_DATA
                    && result != TextToSpeech.LANG_NOT_SUPPORTED;
            if (!ttsReady) {
                Log.e("TTS", "Language not supported");
            }
        } else {
            Log.e("TTS", "Initialization failed");
        }
    }

    @Override
    protected void onStart() {
        super.onStart();
        IntentFilter filter = new IntentFilter(Track.ACTION_UPDATE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(broadcastReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(broadcastReceiver, filter);
        }
        receiverRegistered = true;
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateDrivingModeLabel();
    }

    @Override
    protected void onStop() {
        if (receiverRegistered) {
            unregisterReceiver(broadcastReceiver);
            receiverRegistered = false;
        }
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        mainHandler.removeCallbacksAndMessages(null);
        geocoderExecutor.shutdownNow();
        releaseAlertPlayer();
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
            textToSpeech = null;
        }
        super.onDestroy();
    }
}
