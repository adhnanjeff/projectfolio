package com.example.gpstracker;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.TextView;

import com.google.android.material.button.MaterialButton;

import java.text.DecimalFormat;

public class AnalyticsActivity extends AppCompatActivity {

    private MaterialButton btn_back;
    private TextView total_trips, safety_score, avg_speed, max_speed, violations;
    private RecyclerView recycler_activity;
    private SharedPreferences preferences;
    private static final DecimalFormat df = new DecimalFormat("0.0");

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_analytics);

        initViews();
        setupClickListeners();
        loadAnalyticsData();
        setupRecyclerView();
    }

    private void initViews() {
        btn_back = findViewById(R.id.btn_back);
        total_trips = findViewById(R.id.total_trips);
        safety_score = findViewById(R.id.safety_score);
        avg_speed = findViewById(R.id.avg_speed);
        max_speed = findViewById(R.id.max_speed);
        violations = findViewById(R.id.violations);
        recycler_activity = findViewById(R.id.recycler_activity);
        
        preferences = getSharedPreferences("SafeDrivePrefs", MODE_PRIVATE);
    }

    private void setupClickListeners() {
        btn_back.setOnClickListener(v -> finish());
    }

    private void loadAnalyticsData() {
        // Load data from SharedPreferences or database
        int trips = preferences.getInt("total_trips", 0);
        float safetyScore = preferences.getFloat("safety_score", 85.0f);
        float avgSpeedValue = preferences.getFloat("avg_speed", 45.0f);
        float maxSpeedValue = preferences.getFloat("max_speed", 78.0f);
        int violationCount = preferences.getInt("violations", 0);

        total_trips.setText(String.valueOf(trips));
        safety_score.setText(df.format(safetyScore) + "%");
        avg_speed.setText(df.format(avgSpeedValue) + " km/h");
        max_speed.setText(df.format(maxSpeedValue) + " km/h");
        violations.setText(String.valueOf(violationCount));
    }

    private void setupRecyclerView() {
        recycler_activity.setLayoutManager(new LinearLayoutManager(this));
        // TODO: Setup adapter with recent activity data
    }
}