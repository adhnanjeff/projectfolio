package com.example.gpstracker.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.gpstracker.R;
import com.example.gpstracker.data.EmergencyContact;
import com.google.android.material.button.MaterialButton;

import java.util.ArrayList;
import java.util.List;

public class ContactsAdapter extends RecyclerView.Adapter<ContactsAdapter.ContactViewHolder> {

    public interface Listener {
        void onCall(EmergencyContact contact);

        void onDelete(EmergencyContact contact);
    }

    private final List<EmergencyContact> contacts = new ArrayList<>();
    private final Listener listener;

    public ContactsAdapter(Listener listener) {
        this.listener = listener;
    }

    public void submit(List<EmergencyContact> newContacts) {
        contacts.clear();
        contacts.addAll(newContacts);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ContactViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_contact, parent, false);
        return new ContactViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ContactViewHolder holder, int position) {
        EmergencyContact contact = contacts.get(position);
        holder.name.setText(contact.name);
        holder.phone.setText(contact.phone);
        holder.call.setOnClickListener(v -> listener.onCall(contact));
        holder.delete.setOnClickListener(v -> listener.onDelete(contact));
    }

    @Override
    public int getItemCount() {
        return contacts.size();
    }

    static class ContactViewHolder extends RecyclerView.ViewHolder {
        final TextView name;
        final TextView phone;
        final MaterialButton call;
        final MaterialButton delete;

        ContactViewHolder(@NonNull View itemView) {
            super(itemView);
            name = itemView.findViewById(R.id.contact_name);
            phone = itemView.findViewById(R.id.contact_phone);
            call = itemView.findViewById(R.id.btn_call);
            delete = itemView.findViewById(R.id.btn_delete);
        }
    }
}
