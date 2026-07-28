package com.example.gpstracker;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.data.DangerZone;
import com.example.gpstracker.data.DangerZoneStore;
import com.example.gpstracker.ui.ZonesAdapter;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

import java.util.List;

/** Lets the user add and remove their own accident-prone areas. */
public class DangerZonesActivity extends AppCompatActivity implements ZonesAdapter.Listener {

    private DangerZoneStore store;
    private ZonesAdapter adapter;
    private RecyclerView recycler;
    private TextView empty;
    private FusedLocationProviderClient fusedLocationProviderClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_danger_zones);

        store = new DangerZoneStore(this);
        fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this);

        recycler = findViewById(R.id.recycler_zones);
        empty = findViewById(R.id.empty_zones);
        MaterialButton back = findViewById(R.id.btn_back);
        MaterialButton addManual = findViewById(R.id.btn_add_zone);
        MaterialButton addCurrent = findViewById(R.id.btn_add_current);

        adapter = new ZonesAdapter(this);
        recycler.setLayoutManager(new LinearLayoutManager(this));
        recycler.setAdapter(adapter);

        back.setOnClickListener(v -> finish());
        addManual.setOnClickListener(v -> showAddDialog());
        addCurrent.setOnClickListener(v -> addCurrentLocation());

        refresh();
    }

    private void refresh() {
        List<DangerZone> zones = store.getAll();
        adapter.submit(zones);
        empty.setVisibility(zones.isEmpty() ? View.VISIBLE : View.GONE);
        recycler.setVisibility(zones.isEmpty() ? View.GONE : View.VISIBLE);
    }

    private void showAddDialog() {
        View view = LayoutInflater.from(this).inflate(R.layout.dialog_add_zone, null);
        EditText nameInput = view.findViewById(R.id.input_zone_name);
        EditText latInput = view.findViewById(R.id.input_zone_lat);
        EditText lonInput = view.findViewById(R.id.input_zone_lon);

        new AlertDialog.Builder(this)
                .setTitle(R.string.add_zone)
                .setView(view)
                .setPositiveButton(R.string.save, (dialog, which) -> {
                    String name = nameInput.getText().toString().trim();
                    Double latitude = parseCoordinate(latInput.getText().toString(), 90);
                    Double longitude = parseCoordinate(lonInput.getText().toString(), 180);

                    if (name.isEmpty() || latitude == null || longitude == null) {
                        Snackbar.make(recycler, "Enter a name and valid coordinates",
                                Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    store.add(name, latitude, longitude);
                    refresh();
                })
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }

    /** Returns null when the text is not a number inside the valid coordinate range. */
    private Double parseCoordinate(String raw, double limit) {
        try {
            double value = Double.parseDouble(raw.trim());
            return (value < -limit || value > limit) ? null : value;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private void addCurrentLocation() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            Snackbar.make(recycler, "Location permission is required", Snackbar.LENGTH_LONG).show();
            return;
        }
        fusedLocationProviderClient.getLastLocation().addOnSuccessListener(this, location -> {
            if (location == null) {
                Snackbar.make(recycler, R.string.sos_no_location, Snackbar.LENGTH_LONG).show();
                return;
            }
            store.add("Zone " + (store.getAll().size() + 1),
                    location.getLatitude(), location.getLongitude());
            refresh();
        });
    }

    @Override
    public void onDelete(DangerZone zone) {
        new AlertDialog.Builder(this)
                .setTitle(R.string.delete)
                .setMessage("Remove \"" + zone.name + "\"?")
                .setPositiveButton(R.string.delete, (dialog, which) -> {
                    store.remove(zone.id);
                    refresh();
                })
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }
}
