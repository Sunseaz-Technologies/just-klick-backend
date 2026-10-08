import json
from django import forms
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.categories.models import Category, CategoryField
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from apps.accounts.decorators import superadmin_required
from apps.dynamic.pagination import paginate_queryset
from .models import Category, CategoryField
User = get_user_model()



# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def category_to_dict(cat):
    return {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'image': cat.image.url if cat.image else None,
        'is_active': cat.is_active,
        'created_at': cat.created_at.isoformat(),
        'updated_at': cat.updated_at.isoformat(),
    }


# ─────────────────────────────────────────────
# API Views
# ─────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CategoryListCreateView(LoginRequiredMixin,View):

    def get(self, request):
        categories = Category.objects.all()
        return JsonResponse([category_to_dict(c) for c in categories], safe=False)

    def post(self, request):
        data = request.POST
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)

        cat = Category(name=name, is_active=data.get('is_active', True))
        if request.FILES.get('image'):
            cat.image = request.FILES['image']
        cat.save()
        return JsonResponse(category_to_dict(cat), status=201)


@method_decorator(csrf_exempt, name='dispatch')
class CategoryDetailView(LoginRequiredMixin,View):

    def get_object(self, slug):
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None

    def get(self, request, slug):
        cat = self.get_object(slug)
        if not cat:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse(category_to_dict(cat))

    def put(self, request, slug):
        cat = self.get_object(slug)
        if not cat:
            return JsonResponse({'error': 'Not found'}, status=404)

        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST

        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)

        cat.name = name
        cat.slug = ''
        cat.is_active = data.get('is_active', cat.is_active)
        if request.FILES.get('image'):
            cat.image = request.FILES['image']
        cat.save()
        return JsonResponse(category_to_dict(cat))

    def patch(self, request, slug):
        cat = self.get_object(slug)
        if not cat:
            return JsonResponse({'error': 'Not found'}, status=404)

        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST

        if 'name' in data:
            cat.name = data['name'].strip()
            cat.slug = ''
        if 'is_active' in data:
            cat.is_active = data['is_active']
        if request.FILES.get('image'):
            cat.image = request.FILES['image']
        cat.save()
        return JsonResponse(category_to_dict(cat))

    def delete(self, request, slug):
        cat = self.get_object(slug)
        if not cat:
            return JsonResponse({'error': 'Not found'}, status=404)
        cat.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=200)


# ─────────────────────────────────────────────
# Dashboard HTML Views
# ─────────────────────────────────────────────

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'banner_image', 'subtitle', 'url', 'color', 'is_card', 'order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['banner_image'].required = False
        self.fields['order'].required = False
        self.fields['is_card'].required = False
        self.fields['url'].required = False  


# class CategoryListView(LoginRequiredMixin,View):
#     def get(self, request):
#         categories = Category.objects.all()
#         return render(request, 'categories/list.html', {
#             'categories': categories,
#             'active_tab': 'categories',
#         })

class CategoryListView(LoginRequiredMixin, View):
    def get(self, request):
        queryset = Category.objects.all().order_by('id')

        categories = paginate_queryset(
            request,
            queryset,
            per_page=10
        )
        return render(request, 'categories/list.html', {
            'categories': categories,   # paginated data
            'page_obj': categories,     # for pagination UI
            'active_tab': 'categories',
        })


class CategoryCreateView(LoginRequiredMixin,View):
    def get(self, request):
        form = CategoryForm()
        return render(request, 'categories/form.html', {
            'form': form,
            'active_tab': 'categories',
        })

    def post(self, request):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('categories:list')
        return render(request, 'categories/form.html', {
            'form': form,
            'active_tab': 'categories',
        })


class CategoryEditView(LoginRequiredMixin,View):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        form = CategoryForm(instance=category)
        return render(request, 'categories/form.html', {
            'form': form,
            'category': category,
            'active_tab': 'categories',
        })

    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('categories:list')
        return render(request, 'categories/form.html', {
            'form': form,
            'category': category,
            'active_tab': 'categories',
        })


class CategoryDeleteView(LoginRequiredMixin,View):
    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('categories:list')


# ─────────────────────────────────────────────
# Category Field Management Views
# ─────────────────────────────────────────────

class CategoryFieldForm(forms.ModelForm):
    class Meta:
        model = CategoryField
        fields = ['label', 'field_type', 'options', 'show_as_filter', 'placeholder', 'is_required', 'order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CategoryFieldListView(LoginRequiredMixin,View):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        fields = CategoryField.objects.filter(category=category).order_by('order')
        return render(request, 'categories/fields/list.html', {
            'category': category,
            'fields': fields,
            'active_tab': 'categories',
        })




class CategoryFieldCreateView(LoginRequiredMixin,View):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        form = CategoryFieldForm()

        return render(request, 'categories/fields/form.html', {
            'category': category,
            'form': form,
            'active_tab': 'categories',
        })

    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)

        form = CategoryFieldForm(request.POST)

        if form.is_valid():
            field = form.save(commit=False)

            try:
                field.options = json.loads(
                    request.POST.get('options', '[]')
                )
            except json.JSONDecodeError:
                field.options = []

            field.category = category
            field.save()

            messages.success(
                request,
                f'Field "{field.label}" added successfully.'
            )

            return redirect('categories:fields', slug=slug)

        return render(request, 'categories/fields/form.html', {
            'category': category,
            'form': form,
            'active_tab': 'categories',
        })


class CategoryFieldEditView(LoginRequiredMixin,View):
    def get(self, request, slug, pk):
        category = get_object_or_404(Category, slug=slug)
        field = get_object_or_404(
            CategoryField,
            pk=pk,
            category=category
        )

        form = CategoryFieldForm(instance=field)

        return render(request, 'categories/fields/form.html', {
            'category': category,
            'field': field,
            'form': form,
            'active_tab': 'categories',
        })

    def post(self, request, slug, pk):
        category = get_object_or_404(Category, slug=slug)

        field = get_object_or_404(
            CategoryField,
            pk=pk,
            category=category
        )

        form = CategoryFieldForm(
            request.POST,
            instance=field
        )

        if form.is_valid():
            field = form.save(commit=False)

            try:
                field.options = json.loads(
                    request.POST.get('options', '[]')
                )
            except json.JSONDecodeError:
                field.options = []

            field.save()

            messages.success(
                request,
                f'Field "{field.label}" updated successfully.'
            )

            return redirect('categories:fields', slug=slug)

        return render(request, 'categories/fields/form.html', {
            'category': category,
            'field': field,
            'form': form,
            'active_tab': 'categories',
        })

class CategoryFieldDeleteView(LoginRequiredMixin,View):
    def post(self, request, slug, pk):
        category = get_object_or_404(Category, slug=slug)
        field = get_object_or_404(CategoryField, pk=pk, category=category)
        label = field.label
        field.delete()
        messages.success(request, f'Field "{label}" deleted.')
        return redirect('categories:fields', slug=slug)