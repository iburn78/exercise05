from textwrap import fill
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.views import View

from users.models import User
from ..models import Card, Post, Comment
from ..forms import PostForm, CommentForm
# use info, success, warning to make it consistent with bootstrap5
from django.contrib import messages
from ..tools import post_image_resize, exception_log
from django.urls import resolve
from django.views.static import serve
import os
from django.http import JsonResponse
from django.core import serializers

def vote(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        object_id = request.POST.get('object_id')
        up_down = request.POST.get('up_down')
        object_type = request.POST.get('object')
        if object_type == 'post': 
            object = get_object_or_404(Post, id=object_id)
        elif object_type == 'comment':
            object = get_object_or_404(Comment, id=object_id)
        else: 
            return JsonResponse({"result": "failure"}, status = 400)
        fill_status = 'neither'
        if up_down == 'up':
            if object.likes.all().filter(id=request.user.id).exists():
                object.likes.remove(request.user)
            else:
                object.likes.add(request.user)
                fill_status = 'up'
                if object.dislikes.all().filter(id=request.user.id).exists():
                    object.dislikes.remove(request.user)
        elif up_down == 'down':
            if object.dislikes.all().filter(id=request.user.id).exists():
                object.dislikes.remove(request.user)
            else:
                object.dislikes.add(request.user)
                fill_status = 'down'
                if object.likes.all().filter(id=request.user.id).exists():
                    object.likes.remove(request.user)
        else:
            pass
        ser_instance = serializers.serialize('json', [object])
        return JsonResponse({"instance": ser_instance, "fill_status": fill_status}, status=200)
    return JsonResponse({"result": "failure"}, status = 400)

class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'board/post_create.html'

    def get(self, request, *args, **kwargs):
        selected_card = get_object_or_404(Card, id=kwargs.get('card_id'))
        if not self.request.user.is_authenticated:
            return redirect('login')

        if selected_card.is_official:
            if self.request.user.is_public_card_manager:
                return super().get(request, *args, **kwargs)
            else:
                raise PermissionDenied
        elif selected_card.is_public:
            # anybody can write in public cards
            return super().get(request, *args, **kwargs)
        else:
            if self.request.user == selected_card.owner:
                return super().get(request, *args, **kwargs)
            else:
                raise PermissionDenied

    def form_valid(self, form):
        images = []
        img_field_input = [form.cleaned_data['image1_input'], form.cleaned_data['image2_input'], form.cleaned_data['image3_input'],
                           form.cleaned_data['image4_input'], form.cleaned_data['image5_input'], form.cleaned_data['image6_input'], form.cleaned_data['image7_input']]
        for img in img_field_input:
            if img != None:
                images.append(img)

        if form.cleaned_data['content'] == '' and len(images) == 0:
            messages.warning(self.request, "Enter content or at least 1 image")
            return redirect('post-create', self.kwargs.get('card_id'))

        form.instance.num_images = len(images)
        for i in range(len(images), 7):
            images.append("")
        [form.instance.image1, form.instance.image2, form.instance.image3, form.instance.image4,
            form.instance.image5, form.instance.image6, form.instance.image7] = images
        form.instance.author = self.request.user
        form.instance.card = get_object_or_404(Card, id=self.kwargs.get('card_id'))
        new_post = form.save(commit=False)
        new_post.save()
        form.save_m2m()
        post_image_resize(new_post)
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        card_id = self.kwargs.get('card_id')
        return f'/card/{card_id}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card'] = get_object_or_404(
            Card, id=self.kwargs.get('card_id'))
        context['num_images'] = 0
        return context

    def get_initial(self):
        initial = super().get_initial()
        return initial

class PostDetailView(DetailView): 
    model = Post
    template_name = 'board/post_detail.html'
    form_class = CommentForm
    context_object_name = 'comments'

    def get(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs.get('pk'))
        if post.card.is_public:
            return super().get(request, *args, **kwargs)
        else:
            if not self.request.user.is_authenticated:
                return redirect('login')
            else:
                if self.request.user == post.card.owner:
                    return super().get(request, *args, **kwargs)
                else:
                    raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, id=self.kwargs.get('pk'))
        context['post'] = post
        context['form'] = self.form_class()
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.card.owner or self.request.user == post.author:
            return True
        return False

    def post(self, request, *args, **kwargs):
        card_id = self.get_object().card.id
        self.success_url = f'/card/{card_id}'
        return super().post(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'board/post_create.html'

    def form_valid(self, form):
        images = []
        img_field_input = [form.cleaned_data['image1_input'], form.cleaned_data['image2_input'], form.cleaned_data['image3_input'],
                           form.cleaned_data['image4_input'], form.cleaned_data['image5_input'], form.cleaned_data['image6_input'], form.cleaned_data['image7_input']]
        original_images = [form.instance.image1, form.instance.image2, form.instance.image3,
                           form.instance.image4, form.instance.image5, form.instance.image6, form.instance.image7]
        for i, img in enumerate(img_field_input):
            if img_field_input[i] != original_images[i]:
                try:
                    if original_images[i].name != "":
                        original_images[i].delete()
                except:
                    text = "Exception in delete th_images - class PostUpdateView delete(): " + \
                        original_images[i].name
                    exception_log(text)

            if img != False and img != None:
                images.append(img)

        form.instance.num_images = len(images)
        for i in range(len(images), 7):
            images.append("")
        [form.instance.image1, form.instance.image2, form.instance.image3, form.instance.image4,
            form.instance.image5, form.instance.image6, form.instance.image7] = images

        form.instance.author = self.get_object().author
        rev_post = form.save(commit=False)
        rev_post.save()
        form.save_m2m()
        post_image_resize(rev_post)
        
        redirect_url = redirect(self.get_success_url())
        if rev_post.content == '' and rev_post.num_images == 0:
            messages.warning(self.request, "Post deleted - no content and no images")
            rev_post.delete()

        return redirect_url

    def get_success_url(self) -> str:
        card_id = self.get_object().card.id
        return f'/card/{card_id}'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.card.owner or self.request.user == post.author:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['num_images'] = self.get_object().num_images
        context['th_image1'] = self.get_object().image1s
        context['th_image2'] = self.get_object().image2s
        context['th_image3'] = self.get_object().image3s
        context['th_image4'] = self.get_object().image4s
        context['th_image5'] = self.get_object().image5s
        context['th_image6'] = self.get_object().image6s
        context['th_image7'] = self.get_object().image7s
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['image1_input'] = self.object.image1
        initial['image2_input'] = self.object.image2
        initial['image3_input'] = self.object.image3
        initial['image4_input'] = self.object.image4
        initial['image5_input'] = self.object.image5
        initial['image6_input'] = self.object.image6
        initial['image7_input'] = self.object.image7
        return initial


class PostMediaView(LoginRequiredMixin, UserPassesTestMixin, View):

    def get(self, *args, **kwargs):
        target_file = self.kwargs.get('file')
        target_dir = os.path.dirname(resolve(self.request.path_info).route)
        return serve(self.request, target_file, target_dir)

    def test_func(self):
        userid = str(self.request.user)
        res = ""
        for ch in userid:
            res += str(ord(ch))
        res = res[:7]
        if str(self.kwargs.get('file')).startswith(res):
            return True
        return False
