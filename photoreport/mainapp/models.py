from django.db import models
from django.core.validators import validate_comma_separated_integer_list

from django.conf import settings
from django.core.files import File
from zipfile import ZipFile
from io import BytesIO
import os

from .validators import validate_file_extension, validate_image_extension


class Image(models.Model):
    image = models.ImageField(
        upload_to='images/%Y-%m-%d', validators=validate_image_extension
    )
    thumbnail = models.ImageField(
        upload_to='thumb/%Y-%m-%d', validators=validate_image_extension,
        null=True, blank=True
    )
    caption = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.caption + ' ' + str(self.id))\
            if self.caption else str(self.id)


class Project(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    images = models.ManyToManyField(Image)
    image_order = models.CharField(
        max_length=1000, validators=[validate_comma_separated_integer_list]
    )

    def __str__(self):
        return str(self.name) if self.name else str(self.id)

    @property
    def sorted_images(self):
        images = self.images.all()
        if not self.image_order:
            return list(images)
        try:
            img_order = [int(i) for i in self.image_order.split(',')]
        except:
            return list(images)
        sorted_images = []
        for img_id in img_order:
            sorted_images.append(images.get(id=img_id))
        return sorted_images


class InputFile(models.Model):
    zip_file = models.FileField(
        upload_to="zipinput/%Y-%m-%d", validators=[validate_file_extension]
    )
    project = models.ForeignKey(Project, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    def create_project(self):
        if self.project:
            return self.project
        # If no project associated with input file
        media_path = settings.MEDIA_ROOT
        file_full_path = media_path + str(self.zip_file)
        # Read zipfile
        archive = ZipFile(file_full_path, 'r')
        # Create a new project
        project = Project()
        project.save()

        # Get list of files from zip
        photos = archive.namelist()
        valid_extensions = [
            '.png', '.jpg', '.gif', '.bmp', '.jpeg'
        ]
        for photo in photos:
            if not '.' + photo.split('.')[-1] in valid_extensions:
                continue
            imgdata = archive.read(photo)
            fname = os.path.join("", photo)

            # save photo
            photo_obj = Image()

            io = BytesIO(imgdata)
            photo_obj.image.save(fname, File(io))

            # Add photo to project
            project.images.add(photo_obj)

        # save project to input file
        self.project = project
        self.save()
        return self.project
