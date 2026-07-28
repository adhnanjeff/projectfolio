package com.example.gpstracker;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.data.ActivityEvent;
import com.example.gpstracker.data.TripStore;
import com.example.gpstracker.ui.ActivityAdapter;
import com.google.android.material.button.MaterialButton;

import java.text.DecimalFormat;
import java.util.List;

public class AnalyticsActivity extends AppCompatActivity {

    private static final DecimalFormat df = new DecimalFormat("0.0");

    private TextView total_trips, safety_score, avg_speed, max_speed, violations, distance, empty;
    private RecyclerView recycler_activity;
    private ActivityAdapter adapter;
    private TripStore tripStore;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_analytics);

        tripStore = new TripStore(this);

        total_trips = findViewById(R.id.total_trips);
        safety_score = findViewById(R.id.safety_score);
        avg_speed = findViewById(R.id.avg_speed);
        max_speed = findViewById(R.id.max_speed);
        violations = findViewById(R.id.violations);
        distance = findViewById(R.id.total_distance);
        empty = findViewById(R.id.empty_activity);
        recycler_activity = findViewById(R.id.recycler_activity);

        MaterialButton back = findViewById(R.id.btn_back);
        MaterialButton clear = findViewById(R.id.btn_clear_history);
        back.setOnClickListener(v -> finish());
        clear.setOnClickListener(v -> confirmClear());

        adapter = new ActivityAdapter();
        recycler_activity.setLayoutManager(new LinearLayoutManager(this));
        recycler_activity.setAdapter(adapter);
        // Height is fixed in the layout, so let the parent ScrollView own the scrolling.
        recycler_activity.setNestedScrollingEnabled(false);
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadAnalyticsData();
    }

    private void loadAnalyticsData() {
        total_trips.setText(String.valueOf(tripStore.getTotalTrips()));

        float score = tripStore.getSafetyScore();
        safety_score.setText(df.format(score) + "%");
        safety_score.setTextColor(ContextCompat.getColor(this, colorForScore(score)));

        avg_speed.setText(df.format(tripStore.getAvgSpeed()) + " km/h");
        max_speed.setText(df.format(tripStore.getMaxSpeed()) + " km/h");
        violations.setText(String.valueOf(tripStore.getViolations()));
        distance.setText(df.format(tripStore.getTotalDistanceKm()) + " km");

        List<ActivityEvent> events = tripStore.getEvents();
        adapter.submit(events);
        empty.setVisibility(events.isEmpty() ? View.VISIBLE : View.GONE);
        recycler_activity.setVisibility(events.isEmpty() ? View.GONE : View.VISIBLE);
    }

    private int colorForScore(float score) {
        if (score >= 80f) {
            return R.color.safe_green;
        }
        return score >= 50f ? R.color.warning_orange : R.color.danger_red;
    }

    private void confirmClear() {
        new AlertDialog.Builder(this)
                .setTitle(R.string.clear_history)
                .setMessage("Delete all recorded trips and activity?")
                .setPositiveButton(R.string.delete, (dialog, which) -> {
                    tripStore.clear();
                    loadAnalyticsData();
                })
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }
}
