package com.example.gpstracker;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;

import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationCallback;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class Track extends Service {

    FusedLocationProviderClient fusedLocationProviderClient;
    LocationCallback locationCallback;
    HashMap<Double,Double> locations=new HashMap<Double,Double>();//Creating HashMap

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        locations.put(10.9760560,76.9667759);  //myHouse
        locations.put(37.4219,-122.084);//google
        locations.put(11.101138, 76.965810); //stone bench

        fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this);
        locationCallback = new LocationCallback() {
            @Override
            public void onLocationResult(LocationResult locationResult) {
                super.onLocationResult(locationResult);
                Log.d("myLog ", "Lat is: " + locationResult.getLastLocation().getLatitude() + " Long is " + locationResult.getLastLocation().getLongitude());
                double myLat=locationResult.getLastLocation().getLatitude();
                double myLon=locationResult.getLastLocation().getLongitude();
                double mySpeed=locationResult.getLastLocation().getSpeed()*3.6;
                Log.d("close","The speed is"+locationResult.getLastLocation().getSpeed());
                calculateDanger(myLat,myLon,mySpeed);
            }
        };
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        requestLocation();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel("FOREGROUND_SERVICE_CHANNEL_ID", "Foreground Service Channel", NotificationManager.IMPORTANCE_HIGH);
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);

            Notification.Builder notificationBuilder = new Notification.Builder(this, "FOREGROUND_SERVICE_CHANNEL_ID")
                    .setContentTitle("Service is running")
                    .setContentText("Service enabled")
                    .setSmallIcon(R.mipmap.ic_launcher);

            startForeground(1001, notificationBuilder.build());
        }
        return super.onStartCommand(intent, flags, startId);
    }

    @SuppressLint("VisibleForTests")
    private void requestLocation() {
        LocationRequest locationRequest = new LocationRequest();
        locationRequest.setInterval(5000);
        locationRequest.setPriority(LocationRequest.PRIORITY_HIGH_ACCURACY);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        fusedLocationProviderClient.requestLocationUpdates(locationRequest, locationCallback, Looper.myLooper());
    }


    private double getDistance(double lat1,double lon1,double lat2,double lon2){
        int R=6371;
        double dLat=deg2rad(lat2-lat1);
        double dLon=deg2rad(lon2-lon1);
        double a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(deg2rad(lat1))*Math.cos(deg2rad(lat2))*Math.sin(dLon/2)*Math.sin(dLon/2);
        double c=2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
        double d=R*c;
        return d;
    }

    private double deg2rad(double deg){
        return deg* (Math.PI/180);
    }

    private void calculateDanger(double myLat,double myLon,double mySpeed){
        int size=locations.size();
        ArrayList<Double> distances=new ArrayList<Double>();
        for(Map.Entry m:locations.entrySet()){
            double lat2=(Double)m.getKey();
            double lon2=(Double)m.getValue();
            double dist=getDistance(myLat,myLon,lat2,lon2);
            distances.add(dist);
        }
        Collections.sort(distances);
        double closest=distances.get(0);
        Intent intent=new Intent();
        intent.setAction("distance");
        intent.putExtra("closest",closest);
        //intent.putExtra("speed",mySpeed);
        sendBroadcast(intent);

    }
}
