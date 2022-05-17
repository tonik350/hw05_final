from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Group, Post, User, Comment, Follow
from .forms import PostForm, CommentForm


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, settings.POST_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, group_name):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=group_name)
    post_list = group.posts.select_related('group').all()
    paginator = Paginator(post_list, settings.POST_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group', 'author').all()
    paginator = Paginator(post_list, settings.POST_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author).exists()
    )
    context = {
        'following': following,
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.select_related('group', 'author').get(id=post_id)
    comments_in_post = Comment.objects.select_related('post').filter(
        post_id=post_id
    )
    comment_form = CommentForm()
    context = {
        'post': post,
        'comments': comments_in_post,
        'comment_form': comment_form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    user = request.user
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {
        'form': form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = user
        post.save()
        return redirect('posts:profile', user.username)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        pk=post_id
    )
    if request.user == post.author:
        is_edit = True
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        context = {
            'form': form,
            'is_edit': is_edit,
        }
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post.id)
        return render(request, template, context)
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        pk=post_id
    )
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.select_related('group').filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, settings.POST_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author_object = get_object_or_404(User, username=username)
    if author_object != request.user:
        Follow.objects.select_related('user').get_or_create(
            user=request.user, author=author_object
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author_object = get_object_or_404(User, username=username)
    follower_object = Follow.objects.select_related('user').filter(
        user=request.user,
        author=author_object
    )
    if follower_object.exists():
        follower_object.delete()
    return redirect('posts:profile', username=username)
