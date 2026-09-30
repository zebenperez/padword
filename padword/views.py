from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def preview_server_error(request):
    """Render the production 500 page without raising an exception."""
    return render(request, "500.html", status=500)
