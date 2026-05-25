"""Shared utility: generate Excel template download."""
import pandas as pd
from django.http import HttpResponse


def generate_template_excel(headers, filename='template.xlsx'):
    """Generate an Excel template with header row only."""
    df = pd.DataFrame(columns=headers)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    df.to_excel(response, index=False, engine='openpyxl')
    return response
