package com.example.gpstracker;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;

import com.google.android.material.button.MaterialButton;

public class EmergencyContactsActivity extends AppCompatActivity {

    private MaterialButton btn_back, btn_add_contact, btn_police, btn_ambulance, btn_fire;
    private RecyclerView recycler_contacts;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_emergency_contacts);

        initViews();
        setupClickListeners();
        setupRecyclerView();
    }

    private void initViews() {
        btn_back = findViewById(R.id.btn_back);
        btn_add_contact = findViewById(R.id.btn_add_contact);
        btn_police = findViewById(R.id.btn_police);
        btn_ambulance = findViewById(R.id.btn_ambulance);
        btn_fire = findViewById(R.id.btn_fire);
        recycler_contacts = findViewById(R.id.recycler_contacts);
    }

    private void setupClickListeners() {
        btn_back.setOnClickListener(v -> finish());
        
        btn_add_contact.setOnClickListener(v -> {
            // TODO: Implement add contact functionality
            Toast.makeText(this, "Add contact feature coming soon!", Toast.LENGTH_SHORT).show();
        });

        btn_police.setOnClickListener(v -> callEmergencyService("tel:911"));
        btn_ambulance.setOnClickListener(v -> callEmergencyService("tel:911"));
        btn_fire.setOnClickListener(v -> callEmergencyService("tel:911"));
    }

    private void setupRecyclerView() {
        recycler_contacts.setLayoutManager(new LinearLayoutManager(this));
        // TODO: Setup adapter with emergency contacts
    }

    private void callEmergencyService(String phoneNumber) {
        try {
            Intent callIntent = new Intent(Intent.ACTION_CALL);
            callIntent.setData(Uri.parse(phoneNumber));
            startActivity(callIntent);
        } catch (SecurityException e) {
            Toast.makeText(this, "Phone permission required", Toast.LENGTH_SHORT).show();
        }
    }
}