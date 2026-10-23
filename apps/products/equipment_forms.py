"""Grouped checkboxes shared by admin and manager product forms."""
from typing import Any

from django import forms
from django.db.models import Q

from .models import EquipmentOption


class EquipmentCheckboxes(forms.CheckboxSelectMultiple):
    """Render ordered options as accessible group fieldsets."""

    template_name = 'products/equipment/widget.html'

    class Media:
        css = {'all': ('products/css/equipment.css',)}

    def optgroups(self, name, value, attrs=None):
        groups = {}
        for _, options, _ in super().optgroups(name, value, attrs):
            for option in options:
                item = option['value'].instance
                if item.group_id not in groups:
                    groups[item.group_id] = (item.group.name, [], len(groups))
                groups[item.group_id][1].append(option)
        return list(groups.values())


class EquipmentChoiceField(forms.ModelMultipleChoiceField):
    """Make previously selected inactive options removable in the editor."""

    def label_from_instance(self, obj: EquipmentOption) -> str:
        return obj.name if obj.is_active else f'{obj.name} (отключена)'


class EquipmentFormMixin:
    """Limit new selections to active options and retain old inactive links."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if 'equipment' in self.fields:
            selected = self.instance.equipment.all() if self.instance.pk else []
            self.fields['equipment'].queryset = EquipmentOption.objects.filter(
                Q(is_active=True) | Q(pk__in=selected),
            ).select_related('group')
