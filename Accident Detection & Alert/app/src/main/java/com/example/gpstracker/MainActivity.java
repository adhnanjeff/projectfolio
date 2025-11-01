package com.example.gpstracker;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.animation.ObjectAnimator;
import android.app.Activity;
import android.app.ActivityManager;
import android.app.admin.DevicePolicyManager;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.drawable.GradientDrawable;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Vibrator;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

import java.io.IOException;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity implements TextToSpeech.OnInitListener {

    private LocationManager locationManager;
    private MaterialButton b_enable, b_maps, btn_emergency, btn_settings, btn_history, btn_contacts, btn_analytics;
    private TextView lat, lon, dist, add, status_text, speed;
    private View status_indicator;

    private FusedLocationProviderClient fusedLocationProviderClient;
    private Context mContext;
    private int count = 0;
    private static final int LOCATION_PERMISSION_REQUEST_CODE = 44;
    private static final DecimalFormat df = new DecimalFormat("0.00");

    private DevicePolicyManager devicePolicyManager;
    private ComponentName componentName;
    private TextToSpeech textToSpeech;
    private Vibrator vibrator;
    private SharedPreferences preferences;
    private boolean isDangerZone = false;
    private double currentSpeed = 0;
    private Handler animationHandler = new Handler();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        mContext = this;

        b_enable = findViewById(R.id.b_enable);
        // b_lock = findViewById(R.id.b_lock);
        b_maps = findViewById(R.id.maps);
        lat = findViewById(R.id.lat);
        lon = findViewById(R.id.lon);
        dist = findViewById(R.id.distance);
        add = findViewById(R.id.add);

        devicePolicyManager = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        componentName = new ComponentName(this, Controller.class);

        fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(new Intent(this, Track.class));
        }

        boolean isAdminActive = devicePolicyManager.isAdminActive(componentName);
        b_enable.setText(isAdminActive ? "Disable Driving Mode" : "Enable Driving Mode");

        b_enable.setOnClickListener(v -> {
            if (devicePolicyManager.isAdminActive(componentName)) {
                devicePolicyManager.removeActiveAdmin(componentName);
                b_enable.setText("Enable Driving Mode");
            } else {
                Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
                intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, componentName);
                intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "Please enable driving mode.");
                startActivity(intent);
                b_enable.setText("Disable Driving Mode");
            }
        });

        b_maps.setOnClickListener(v -> {
            String geoUri = "geo:0,0?q=" + lat.getText() + "," + lon.getText() + "(Your Location)";
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(geoUri));
            intent.setPackage("com.google.android.apps.maps");
            startActivity(intent);
        });

        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        checkLocationPermission();
        registerReceiver(broadcastReceiver, new IntentFilter("distance"));
    }

    private void checkLocationPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, LOCATION_PERMISSION_REQUEST_CODE);
        } else {
            setupLocationUpdates();
            isLocationEnabled();
        }
    }

    private void setupLocationUpdates() {
        locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 2000, 10, locationListenerGPS);
    }

    private final LocationListener locationListenerGPS = new LocationListener() {
        @Override
        public void onLocationChanged(@NonNull Location location) {
            double latitude = location.getLatitude();
            double longitude = location.getLongitude();
            lat.setText("Latitude: " + df.format(latitude));
            lon.setText("Longitude: " + df.format(longitude));
        }
    };

    private void isLocationEnabled() {
        if (!locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
            new AlertDialog.Builder(this)
                    .setTitle("Enable Location")
                    .setMessage("Location is disabled. Enable it in settings?")
                    .setPositiveButton("Yes", (dialog, which) -> startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)))
                    .setNegativeButton("Cancel", (dialog, which) -> dialog.dismiss())
                    .show();
        } else {
            getLocation();
        }
    }

    private void getLocation() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return;

        fusedLocationProviderClient.getLastLocation().addOnCompleteListener(task -> {
            Location location = task.getResult();
            if (location != null) {
                Geocoder geocoder = new Geocoder(this, Locale.getDefault());
                try {
                    List<Address> addresses = geocoder.getFromLocation(location.getLatitude(), location.getLongitude(), 1);
                    if (addresses != null && !addresses.isEmpty()) {
                        Address address = addresses.get(0);
                        double myLat = address.getLatitude();
                        double myLon = address.getLongitude();
                        String addressLine = address.getAddressLine(0);
                        lat.setText("Latitude: " + df.format(myLat));
                        lon.setText("Longitude: " + df.format(myLon));
                        add.setText("Your current location:\n" + addressLine);
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        isLocationEnabled();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(broadcastReceiver);
    }

    private final BroadcastReceiver broadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            double closest = intent.getDoubleExtra("closest", 0);
            if (closest < 1) {
                closest *= 1000;
                dist.setText("Closest accident-prone area: " + df.format(closest) + " metres");
            } else {
                dist.setText("Closest accident-prone area: " + df.format(closest) + " km");
            }

            if (closest > 1.5) {
                count = 0;
            }

            if (closest <= 1.5) {
                if (count == 1) {
                    MediaPlayer mp = MediaPlayer.create(MainActivity.this, R.raw.accident);
                    mp.start();
                }

                if (devicePolicyManager.isAdminActive(componentName) && count == 0) {
                    Toast.makeText(getApplicationContext(), "Entering accident-prone zone. Screen will lock unless driving mode is disabled.", Toast.LENGTH_LONG).show();
                    new Handler().postDelayed(() -> {
                        if (devicePolicyManager.isAdminActive(componentName)) {
                            try {
                                devicePolicyManager.lockNow();
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }
                    }, 10000);
                }

                count++;
                if (count == 30) count = 0;
            }
        }
    };
}
