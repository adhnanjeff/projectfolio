package com.example.gpstracker;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;
import android.telephony.SmsManager;
import android.util.Log;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.example.gpstracker.data.ActivityEvent;
import com.example.gpstracker.data.ContactStore;
import com.example.gpstracker.data.EmergencyContact;
import com.example.gpstracker.data.TripStore;

import java.util.List;
import java.util.Locale;

/** Builds and sends the SOS message to every saved emergency contact. */
public class SosHelper {

    private static final String TAG = "SosHelper";

    private SosHelper() {
    }

    /**
     * Sends an SOS SMS containing a maps link to all saved contacts.
     *
     * @return the number of contacts messaged, or -1 if SMS permission is missing.
     */
    public static int sendSos(Activity activity, double latitude, double longitude) {
        ContactStore contactStore = new ContactStore(activity);
        List<EmergencyContact> contacts = contactStore.getAll();

        if (contacts.isEmpty()) {
            Toast.makeText(activity, R.string.sos_no_contacts, Toast.LENGTH_LONG).show();
            return 0;
        }

        if (ContextCompat.checkSelfPermission(activity, Manifest.permission.SEND_SMS)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(activity,
                    new String[]{Manifest.permission.SEND_SMS}, MainActivity.SMS_PERMISSION_REQUEST_CODE);
            return -1;
        }

        String message = buildMessage(activity, latitude, longitude);
        SmsManager smsManager = getSmsManager(activity);
        int sent = 0;

        for (EmergencyContact contact : contacts) {
            try {
                // Long messages must be split, or the send silently fails on some carriers.
                smsManager.sendMultipartTextMessage(
                        contact.phone, null, smsManager.divideMessage(message), null, null);
                sent++;
            } catch (Exception e) {
                Log.e(TAG, "Failed to send SOS to " + contact.name, e);
            }
        }

        new TripStore(activity).addEvent(ActivityEvent.TYPE_SOS,
                "SOS sent to " + sent + " contact(s)");
        return sent;
    }

    private static String buildMessage(Activity activity, double latitude, double longitude) {
        return String.format(Locale.US,
                "EMERGENCY: I may have been in an accident. My location: %.6f, %.6f\n"
                        + "https://maps.google.com/?q=%.6f,%.6f\n"
                        + "Sent automatically by %s.",
                latitude, longitude, latitude, longitude, activity.getString(R.string.app_name));
    }

    @SuppressWarnings("deprecation")
    private static SmsManager getSmsManager(Activity activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return activity.getSystemService(SmsManager.class);
        }
        return SmsManager.getDefault();
    }
}
