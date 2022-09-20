from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator

from .forms import PostForm, CommentForm

from .models import Comment, Follow, Group, Post, User


def page_obj(posts, request):
    return Paginator(
        posts, settings.POSTS_PER_PAGES
    ).get_page(request.GET.get('page'))


def index(request):
    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj(Post.objects.all(), request)}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj(group.posts.all(), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = user.is_authenticated and author.following.exists()
    return render(
        request,
        'posts/profile.html', {
            'author': author,
            'page_obj': page_obj(author.posts.all(), request),
            'following': following
        }
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments
        }
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    return render(
        request,
        'posts/create_post.html', {
            'post': post,
            'form': form,
        }
    )


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': page_obj(
                Post.objects.filter(author__following__user=request.user),
                request
            )
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return redirect('posts:profile', username)