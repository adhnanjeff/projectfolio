package com.example.gpstracker.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.R;
import com.example.gpstracker.data.ActivityEvent;

import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class ActivityAdapter extends RecyclerView.Adapter<ActivityAdapter.EventViewHolder> {

    private final List<ActivityEvent> events = new ArrayList<>();
    private final DateFormat dateFormat = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT);

    public void submit(List<ActivityEvent> newEvents) {
        events.clear();
        events.addAll(newEvents);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public EventViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_activity, parent, false);
        return new EventViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull EventViewHolder holder, int position) {
        ActivityEvent event = events.get(position);
        holder.message.setText(event.message);
        holder.timestamp.setText(dateFormat.format(new Date(event.timestamp)));
        holder.dot.setBackgroundColor(
                ContextCompat.getColor(holder.itemView.getContext(), colorFor(event.type)));
    }

    private int colorFor(String type) {
        if (ActivityEvent.TYPE_SOS.equals(type) || ActivityEvent.TYPE_DANGER.equals(type)) {
            return R.color.danger_red;
        }
        if (ActivityEvent.TYPE_VIOLATION.equals(type)) {
            return R.color.warning_orange;
        }
        return R.color.safe_green;
    }

    @Override
    public int getItemCount() {
        return events.size();
    }

    static class EventViewHolder extends RecyclerView.ViewHolder {
        final TextView message;
        final TextView timestamp;
        final View dot;

        EventViewHolder(@NonNull View itemView) {
            super(itemView);
            message = itemView.findViewById(R.id.event_message);
            timestamp = itemView.findViewById(R.id.event_time);
            dot = itemView.findViewById(R.id.event_dot);
        }
    }
}
