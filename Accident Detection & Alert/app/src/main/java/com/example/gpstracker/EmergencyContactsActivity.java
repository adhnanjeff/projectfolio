package com.example.gpstracker;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.data.ContactStore;
import com.example.gpstracker.data.EmergencyContact;
import com.example.gpstracker.ui.ContactsAdapter;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

import java.util.List;

public class EmergencyContactsActivity extends AppCompatActivity implements ContactsAdapter.Listener {

    private static final int CALL_PERMISSION_REQUEST_CODE = 47;

    private ContactStore store;
    private ContactsAdapter adapter;
    private RecyclerView recycler;
    private TextView empty;
    private EmergencyContact pendingCall;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_emergency_contacts);

        store = new ContactStore(this);

        recycler = findViewById(R.id.recycler_contacts);
        empty = findViewById(R.id.empty_contacts);
        MaterialButton back = findViewById(R.id.btn_back);
        MaterialButton addContact = findViewById(R.id.btn_add_contact);
        MaterialButton police = findViewById(R.id.btn_police);
        MaterialButton ambulance = findViewById(R.id.btn_ambulance);
        MaterialButton fire = findViewById(R.id.btn_fire);

        adapter = new ContactsAdapter(this);
        recycler.setLayoutManager(new LinearLayoutManager(this));
        recycler.setAdapter(adapter);

        back.setOnClickListener(v -> finish());
        addContact.setOnClickListener(v -> showAddDialog());

        // Emergency services open the dialer pre-filled rather than placing the call
        // outright, so a stray tap cannot dial emergency services by accident.
        police.setOnClickListener(v -> openDialer(getString(R.string.emergency_police_number)));
        ambulance.setOnClickListener(v -> openDialer(getString(R.string.emergency_ambulance_number)));
        fire.setOnClickListener(v -> openDialer(getString(R.string.emergency_fire_number)));

        refresh();
    }

    private void refresh() {
        List<EmergencyContact> contacts = store.getAll();
        adapter.submit(contacts);
        empty.setVisibility(contacts.isEmpty() ? View.VISIBLE : View.GONE);
        recycler.setVisibility(contacts.isEmpty() ? View.GONE : View.VISIBLE);
    }

    private void showAddDialog() {
        View view = LayoutInflater.from(this).inflate(R.layout.dialog_add_contact, null);
        EditText nameInput = view.findViewById(R.id.input_name);
        EditText phoneInput = view.findViewById(R.id.input_phone);

        new AlertDialog.Builder(this)
                .setTitle(R.string.add_contact)
                .setView(view)
                .setPositiveButton(R.string.save, (dialog, which) -> {
                    String name = nameInput.getText().toString().trim();
                    String phone = phoneInput.getText().toString().trim();
                    if (name.isEmpty() || phone.isEmpty()) {
                        Snackbar.make(recycler, "Enter a name and phone number",
                                Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    store.add(name, phone);
                    refresh();
                })
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }

    @Override
    public void onCall(EmergencyContact contact) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE)
                == PackageManager.PERMISSION_GRANTED) {
            placeCall(contact.phone);
        } else {
            pendingCall = contact;
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CALL_PHONE}, CALL_PERMISSION_REQUEST_CODE);
        }
    }

    @Override
    public void onDelete(EmergencyContact contact) {
        new AlertDialog.Builder(this)
                .setTitle(R.string.delete)
                .setMessage("Remove " + contact.name + " from emergency contacts?")
                .setPositiveButton(R.string.delete, (dialog, which) -> {
                    store.remove(contact.id);
                    refresh();
                })
                .setNegativeButton(R.string.cancel, (dialog, which) -> dialog.dismiss())
                .show();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != CALL_PERMISSION_REQUEST_CODE) {
            return;
        }
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED
                && pendingCall != null) {
            placeCall(pendingCall.phone);
        } else if (pendingCall != null) {
            // Without the permission we can still hand the number to the dialer.
            openDialer(pendingCall.phone);
        }
        pendingCall = null;
    }

    private void placeCall(String number) {
        Intent intent = new Intent(Intent.ACTION_CALL, Uri.parse("tel:" + number));
        try {
            startActivity(intent);
        } catch (SecurityException e) {
            openDialer(number);
        }
    }

    private void openDialer(String number) {
        Intent intent = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + number));
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivity(intent);
        } else {
            Snackbar.make(recycler, "No dialer app available", Snackbar.LENGTH_LONG).show();
        }
    }
}
