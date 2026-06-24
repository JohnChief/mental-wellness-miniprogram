from .models import Registration


def remaining_capacity(event):
    if event.capacity is None:
        return None
    used = Registration.query.filter_by(event_id=event.id, status="registered").count()
    checked_in = Registration.query.filter_by(event_id=event.id, status="checked_in").count()
    return max(event.capacity - used - checked_in, 0)


def event_to_dict(event, include_detail=False):
    data = {
        "id": event.id,
        "title": event.title,
        "subtitle": event.subtitle,
        "cover_image": event.cover_image,
        "cover_color": event.cover_color,
        "event_time": event.event_time.isoformat(),
        "event_time_text": event.event_time_text,
        "location": event.location,
        "price_text": event.price_text,
        "category": event.category,
        "remaining": remaining_capacity(event),
    }
    if include_detail:
        data.update(
            {
                "description": event.description,
                "target_audience": event.target_audience,
                "flow": event.flow,
                "notice": event.notice,
                "registration_deadline": (
                    event.registration_deadline.isoformat()
                    if event.registration_deadline
                    else None
                ),
            }
        )
    return data


def registration_to_dict(registration):
    return {
        "id": registration.id,
        "status": registration.status,
        "name": registration.name,
        "phone": registration.phone,
        "remark": registration.remark,
        "checked_in_at": (
            registration.checked_in_at.isoformat()
            if registration.checked_in_at
            else None
        ),
        "created_at": registration.created_at.isoformat(),
        "event": event_to_dict(registration.event, include_detail=False),
    }
