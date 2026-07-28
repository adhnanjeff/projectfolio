package com.example.gpstracker.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.R;
import com.example.gpstracker.data.DangerZone;
import com.google.android.material.button.MaterialButton;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class ZonesAdapter extends RecyclerView.Adapter<ZonesAdapter.ZoneViewHolder> {

    public interface Listener {
        void onDelete(DangerZone zone);
    }

    private final List<DangerZone> zones = new ArrayList<>();
    private final Listener listener;

    public ZonesAdapter(Listener listener) {
        this.listener = listener;
    }

    public void submit(List<DangerZone> newZones) {
        zones.clear();
        zones.addAll(newZones);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ZoneViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_zone, parent, false);
        return new ZoneViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ZoneViewHolder holder, int position) {
        DangerZone zone = zones.get(position);
        holder.name.setText(zone.name);
        holder.coords.setText(String.format(Locale.US, "%.5f, %.5f", zone.latitude, zone.longitude));
        holder.delete.setOnClickListener(v -> listener.onDelete(zone));
    }

    @Override
    public int getItemCount() {
        return zones.size();
    }

    static class ZoneViewHolder extends RecyclerView.ViewHolder {
        final TextView name;
        final TextView coords;
        final MaterialButton delete;

        ZoneViewHolder(@NonNull View itemView) {
            super(itemView);
            name = itemView.findViewById(R.id.zone_name);
            coords = itemView.findViewById(R.id.zone_coords);
            delete = itemView.findViewById(R.id.btn_delete_zone);
        }
    }
}
