from datetime import timedelta

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import staff_required
from catalog.models import Product, ProductQuestion, ProductReview
from orders.models import Order

from .forms import ReportFilterForm
from .services import build_report, report_to_pdf, report_to_xlsx


@staff_required
def dashboard(request):
    today = timezone.localdate()
    data = build_report(today - timedelta(days=29), today, today)
    recent_orders = Order.objects.select_related("user").prefetch_related("items")[:6]
    status_counts = dict(Order.objects.values_list("status").annotate(total=Count("id")))
    return render(
        request,
        "staff/dashboard.html",
        {
            "report": data,
            "low_stock": Product.objects.filter(is_active=True, stock__lte=5).count(),
            "recent_orders": recent_orders,
            "status_counts": status_counts,
            "unanswered_feedback": ProductReview.objects.filter(admin_reply="").count() + ProductQuestion.objects.filter(answer="").count(),
        },
    )


@staff_required
def reports_view(request):
    form = ReportFilterForm(request.GET or None)
    data = None
    if form.is_valid():
        data = build_report(**form.cleaned_data)
        export_format = request.GET.get("format")
        stamp = f"{data['date_from'].isoformat()}_{data['date_to'].isoformat()}"
        if export_format == "xlsx":
            response = HttpResponse(report_to_xlsx(data), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = f'attachment; filename="autoparts-report-{stamp}.xlsx"'
            return response
        if export_format == "pdf":
            response = HttpResponse(report_to_pdf(data), content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="autoparts-report-{stamp}.pdf"'
            return response
    return render(request, "staff/reports.html", {"form": form, "report": data})
