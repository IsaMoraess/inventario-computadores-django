from django import forms

from .models import Computador, ConfiguracaoSistema, Planta


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


class PlantaForm(forms.ModelForm):
    definir_ativa = forms.BooleanField(
        label='Definir como planta ativa',
        required=False,
        initial=True,
    )

    class Meta:
        model = Planta
        fields = ['nome', 'imagem']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nome'].required = True
        self.fields['nome'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Planta principal',
            }
        )
        self.fields['imagem'].widget.attrs.update(
            {
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,image/png,image/jpeg',
            }
        )
        self.fields['definir_ativa'].widget.attrs['class'] = 'toggle-input'

    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')

        if not imagem:
            raise forms.ValidationError('Selecione uma imagem da planta.')

        extensao = imagem.name.rsplit('.', 1)[-1].lower() if '.' in imagem.name else ''
        if extensao not in {'png', 'jpg', 'jpeg'}:
            raise forms.ValidationError('Envie uma imagem PNG, JPG ou JPEG.')

        content_type = getattr(imagem, 'content_type', '')
        if content_type and content_type not in {'image/png', 'image/jpeg'}:
            raise forms.ValidationError('O arquivo precisa ser uma imagem PNG, JPG ou JPEG.')

        return imagem


class ConfiguracaoSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema
        fields = [
            'nome_empresa',
            'logo',
            'cor_principal',
            'cor_secundaria',
            'cor_cards',
            'tema',
            'rodape_pdfs',
            'app_public_url',
        ]
        widgets = {
            'cor_principal': forms.TextInput(attrs={'type': 'color'}),
            'cor_secundaria': forms.TextInput(attrs={'type': 'color'}),
            'cor_cards': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            'nome_empresa': 'JR Grupo',
            'rodape_pdfs': 'JR Grupo - Gestao de Ativos de TI',
            'app_public_url': 'https://inventario.jrgrupo.com.br',
        }

        for name, field in self.fields.items():
            classes = ['form-control']
            if isinstance(field.widget, forms.Select):
                classes.append('form-select')
            field.widget.attrs['class'] = ' '.join(classes)
            if name in placeholders:
                field.widget.attrs.setdefault('placeholder', placeholders[name])

        self.fields['logo'].widget.attrs.update(
            {
                'accept': '.png,.jpg,.jpeg,image/png,image/jpeg',
            }
        )
