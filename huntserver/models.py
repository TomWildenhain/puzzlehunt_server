from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.html import escape
from django.utils.dateformat import DateFormat
from dateutil import tz
from django.conf import settings
time_zone = tz.gettz(settings.TIME_ZONE)

# Create your models here.
class Hunt(models.Model):
    hunt_name = models.CharField(max_length=200)
    hunt_number = models.IntegerField(unique=True)
    team_size = models.IntegerField()
    #Very bad things could happen if end date is before start date
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=100)
    is_current_hunt = models.BooleanField(default=False)
    
    # A bit of custom logic in clean and save to ensure exactly one hunt's
    # is_current_hunt is true at any time. Basically, you can never un-set that
    # value, and setting it anywhere else unsets all others.
    def clean(self, *args, **kwargs):
        if(not self.is_current_hunt):
            try:
                old_instance = Hunt.objects.get(pk=self.pk)
                if(old_instance.is_current_hunt):
                    raise ValidationError({'is_current_hunt': ["There must always be one current hunt",]})
            except ObjectDoesNotExist:
                pass
        super(Hunt, self).clean(*args, **kwargs)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_current_hunt:
            Hunt.objects.filter(is_current_hunt=True).update(is_current_hunt=False)
        super(Hunt, self).save(*args, **kwargs)

    @property
    def is_locked(self):
        return timezone.now() < self.start_date

    @property
    def is_open(self):
        return timezone.now() > self.start_date and timezone.now() < self.end_date

    @property
    def is_public(self):
        return timezone.now() > self.end_date

    def __unicode__(self):
        if(self.is_current_hunt):
            return self.hunt_name + " (c)"
        else:
            return self.hunt_name

class Puzzle(models.Model):
    puzzle_number = models.IntegerField()
    puzzle_name = models.CharField(max_length=200)
    puzzle_id = models.CharField(max_length=8, unique=True) #hex only please
    answer = models.CharField(max_length=100)
    link = models.URLField(max_length=200)
    num_required_to_unlock = models.IntegerField(default=1)
    unlocks = models.ManyToManyField("self", blank=True, symmetrical=False)
    hunt = models.ForeignKey(Hunt)
    num_pages = models.IntegerField()
    
    def serialize_for_ajax(self):
        message = dict()
        message['id'] = self.puzzle_id
        message['number'] = self.puzzle_number
        message['name'] = self.puzzle_name
        return message

    def __unicode__(self):
        return str(self.puzzle_number) + "-" + str(self.puzzle_id) + " " + self.puzzle_name
    
class Team(models.Model):
    team_name = models.CharField(max_length=200)
    solved = models.ManyToManyField(Puzzle, blank=True, related_name='solved_for', through="Solve")
    unlocked = models.ManyToManyField(Puzzle, blank=True, related_name='unlocked_for', through="Unlock")
    unlockables = models.ManyToManyField("Unlockable", blank=True)
    hunt = models.ForeignKey(Hunt)
    location = models.CharField(max_length=80, blank=True)
    join_code = models.CharField(max_length=5)
    playtester = models.BooleanField(default=False)

    @property
    def is_playtester_team(self):
        return self.playtester

    @property
    def is_normal_team(self):
        return (not self.playtester)

    def __unicode__(self):
        return str(len(self.person_set.all())) + " (" + self.location + ") " + self.team_name

class Person(models.Model):
    user = models.OneToOneField(User)
    phone = models.CharField(max_length=20, blank=True)
    allergies = models.CharField(max_length=400, blank=True)
    comments = models.CharField(max_length=400, blank=True)
    teams = models.ManyToManyField(Team, blank=True)
    is_shib_acct = models.BooleanField()
    
    def __unicode__(self):
        name = self.user.first_name + " " + self.user.last_name + " (" + self.user.email + ")"
        if(name == " "):
            return "Anonymous User"
        else:
            return self.user.first_name + " " + self.user.last_name + " (" + self.user.email + ")"
    
class Submission(models.Model):
    team = models.ForeignKey(Team)
    submission_time = models.DateTimeField()
    submission_text = models.CharField(max_length=100)
    response_text = models.CharField(blank=True, max_length=400)
    puzzle = models.ForeignKey(Puzzle)
    modified_date = models.DateTimeField()

    def serialize_for_ajax(self):
        message = dict()
        df = DateFormat(self.submission_time.astimezone(time_zone))
        message['time_str'] = df.format("h:i a")
        message['submission_text'] = escape(self.submission_text)
        message['response_text'] = escape(self.response_text)
        message['is_correct'] = self.is_correct
        message['puzzle'] = self.puzzle.serialize_for_ajax()
        message['team'] = self.team.team_name
        message['pk'] = self.pk
        return message

    @property
    def is_correct(self):
        return self.submission_text.lower() == self.puzzle.answer.lower()

    def save(self, *args, **kwargs):
        self.modified_date = timezone.now()
        super(Submission,self).save(*args, **kwargs)
    
    def __unicode__(self):
        return self.submission_text

class Solve(models.Model):
    puzzle = models.ForeignKey(Puzzle)
    team = models.ForeignKey(Team)
    submission = models.ForeignKey(Submission, blank=True)

    class Meta:
        unique_together = ('puzzle', 'team',)

    def serialize_for_ajax(self):
        message = dict()
        message['puzzle'] = self.puzzle.serialize_for_ajax()
        message['team_pk'] = self.team.pk
        try:
            # Will fail if there is more than one solve per team/puzzle pair
            # That should be impossible, but lets not crash because of it
            time = self.submission.submission_time
            df = DateFormat(time.astimezone(time_zone))
            message['time_str'] = df.format("h:i a")
        except:
            message['time_str'] = "0:00 am"
        message['status_type'] = "solve"
        return message
    
    def __unicode__(self):
        return self.team.team_name + " => " + self.puzzle.puzzle_name
    
class Unlock(models.Model):
    puzzle = models.ForeignKey(Puzzle)
    team = models.ForeignKey(Team)
    time = models.DateTimeField()

    class Meta:
        unique_together = ('puzzle', 'team',)
    
    def serialize_for_ajax(self):
        message = dict()
        message['puzzle'] = self.puzzle.serialize_for_ajax()
        message['team_pk'] = self.team.pk
        message['status_type'] = "unlock"
        return message

    def __unicode__(self):
        return self.team.team_name + ": " + self.puzzle.puzzle_name

class Message(models.Model):
    team = models.ForeignKey(Team)
    is_response = models.BooleanField()
    text = models.CharField(max_length=400)
    time = models.DateTimeField()

    def __unicode__(self):
        return unicode(self.team.team_name + ": " + self.text)

class Unlockable(models.Model):
    TYPE_CHOICES = (
        ('IMG', 'Image'),
        ('PDF', 'PDF'),
        ('TXT', 'Text'),
        ('WEB', 'Link'),
    )
    puzzle = models.ForeignKey(Puzzle)
    content_type = models.CharField(max_length=3, choices=TYPE_CHOICES, default='TXT')
    content = models.CharField(max_length=500)

    def __unicode__(self):
        return "%s (%s)" % (self.puzzle.puzzle_name, self.content_type)
    
class Response(models.Model):
    puzzle = models.ForeignKey(Puzzle)
    regex = models.CharField(max_length=400)
    text = models.CharField(max_length=400)

    def __unicode__(self):
        return self.regex + "=>" + self.text
