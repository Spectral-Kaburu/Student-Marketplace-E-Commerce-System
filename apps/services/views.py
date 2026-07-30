from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.contrib import messages

from .models import Service, ServiceImage
from .forms import ServiceForm, ServiceImageForm


def service_list(request):
    services = Service.objects.filter(is_available=True).order_by("-created_at")

    query = request.GET.get('q')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    # No `category` filter -- Service has no category field.

    if query:
        services = services.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if price_min:
        services = services.filter(price__gte=price_min)
    if price_max:
        services = services.filter(price__lte=price_max)

    context = {"services": services}
    if request.headers.get('HX-Request'):
        return HttpResponse(render_to_string('services/_listing_grid.html', context, request=request))

    return render(request, "services/service_list.html", context)


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return render(request, "services/service_detail.html", {
        "service": service
    })


@login_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        image_form = ServiceImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            service = form.save(commit=False)
            service.seller = request.user
            service.save()
            # Handle multiple image uploads
            images = request.FILES.getlist('image')
            for image in images:
                if image:
                    ServiceImage.objects.create(service=service, image=image)
            return redirect("service_detail", pk=service.pk)
    else:
        form = ServiceForm()
        image_form = ServiceImageForm()

    return render(request, "services/service_form.html", {
        "form": form,
        "image_form": image_form,
        "action": "Create"
    })


@login_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if service.seller != request.user:
        raise PermissionDenied("Only the seller can edit this listing.")

    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        image_form = ServiceImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            service = form.save()
            images = request.FILES.getlist('image')
            for image in images:
                if image:
                    ServiceImage.objects.create(service=service, image=image)
            return redirect("service_detail", pk=service.pk)
    else:
        form = ServiceForm(instance=service)
        image_form = ServiceImageForm()

    return render(request, "services/service_form.html", {
        "form": form,
        "image_form": image_form,
        "action": "Update",
        "object": service,  # <--- Pass object here!
    })


@login_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if service.seller != request.user:
        raise PermissionDenied("Only the seller can delete this listing.")

    if request.method == "POST":
        service.delete()
        return redirect("service_list")

    return render(request, "services/service_confirm_delete.html", {
        "service": service
    })


@login_required
def service_image_delete(request, pk):
    image = get_object_or_404(ServiceImage, pk=pk)
    if image.service.seller != request.user:
        raise PermissionDenied("Only the seller can delete this image.")

    if request.method == "POST":
        service_pk = image.service.pk
        image.delete()
        messages.success(request, "Image deleted successfully.")
        return redirect("service_update", pk=service_pk)

    return render(request, "services/service_image_confirm_delete.html", {
        "image": image
    })
