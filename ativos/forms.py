from django import forms

from .models import Computador


class ComputadorForm(forms.ModelForm):
    class Meta:
        model = Computador
        fields = [
            'id',
            'sala',
            'x',
            'y',
            'status',
            'armazenamento',
            'placa_video',
            'usuario',
            'sistema',
            'ram',
            'processador',
            'observacoes',
        ]
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['id'].disabled = True

        for field in self.fields.values():
            classes = ['form-control']
            if isinstance(field.widget, forms.Select):
                classes.append('form-select')
            field.widget.attrs['class'] = ' '.join(classes)

        self.fields['id'].widget.attrs.setdefault('placeholder', 'ETJR01')
        self.fields['sala'].widget.attrs.setdefault('placeholder', 'Recepcao')
        self.fields['usuario'].widget.attrs.setdefault('placeholder', 'Nome do usuario')

    def clean_id(self):
        computador_id = (self.cleaned_data.get('id') or '').strip()

        if not computador_id:
            raise forms.ValidationError('Informe o ID do computador.')

        queryset = Computador.objects.filter(pk=computador_id)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError('Ja existe um computador com este ID.')

        return computador_id
