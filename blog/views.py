from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage,\
                                  PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST


def post_list(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not and integer, return the first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range, return the last page.
        posts = paginator.page(paginator.num_pages)
    
    return render(request, 'blog/post/list.html',
                           {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()
    return render(request, 'blog/post/detail.html',
                           {'post': post,
                            'comments': comments,
                            'form': form})


class PostListView(ListView):
    """
    Alternative for post_list function view.
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Get post by id
    post = get_object_or_404(Post, id=post_id, \
                                   status=Post.Status.PUBLISHED)
    sent = False
    
    if request.method == 'POST':
        # Form submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Fields verified successfully
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'conillatte@gmail.com',
                        [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                           {'post': post,
                            'form': form,
                            'sent': sent})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # A comment has been posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object not saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return render(request, 'blog/post/comment.html',
                           {'post':post,
                            'form': form,
                            'comment': comment})
