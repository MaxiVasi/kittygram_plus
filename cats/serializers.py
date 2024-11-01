from rest_framework import serializers
import webcolors

import datetime as dt

from .models import Achievement, Cat, Owner, AchievementCat, CHOICES


class AchievementSerializer(serializers.ModelSerializer):
    # Переименование переопределение полей
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class Hex2NameColor(serializers.Field):

    # При чтении данных ничего не меняем - просто возвращаем как есть
    def to_representation(self, value):
        return value

    # При записи код цвета конвертируется в его название
    def to_internal_value(self, data):
        # Доверяй, но проверяй
        try:
            # Если имя цвета существует, то конвертируем код в название
            data = webcolors.hex_to_name(data)
        except ValueError:
            # Иначе возвращаем ошибку
            raise serializers.ValidationError('Для этого цвета нет имени')
        # Возвращаем данные в новом формате
        return data


class CatSerializer(serializers.ModelSerializer):
    # Роль StringRelatedField — получить строковые представления связанных
    # объектов и передать их в указанное поле вместо id.
    # owner = serializers.StringRelatedField(read_only=True)
    # Переопределяем поле achievements
    # achievements = AchievementSerializer(read_only=True, many=True)

    achievements = AchievementSerializer(many=True, required=False)
    # Вычисляем возраст котика.
    age = serializers.SerializerMethodField()
    # добавляем поле color
    # color = Hex2NameColor()
    # Теперь поле примет только значение, упомянутое в списке CHOICES
    # color = serializers.ChoiceField(choices=CHOICES)

    def create(self, validated_data):
        # Если в исходном запросе не было поля achievements
        if 'achievements' not in self.initial_data:
            # То создаём запись о котике без его достижений
            cat = Cat.objects.create(**validated_data)
            return cat

        # Иначе делаем следующее:
        # Уберём список достижений из словаря validated_data и сохраним его
        achievements = validated_data.pop('achievements')

        # Создадим нового котика пока без достижений, данных нам достаточно
        # Сначала добавляем котика в БД
        cat = Cat.objects.create(**validated_data)

        # Для каждого достижения из списка достижений
        for achievement in achievements:
            # Создадим новую запись или получим существующий экземпляр из БД
            current_achievement, status = Achievement.objects.get_or_create(
                **achievement)
            # Поместим ссылку на каждое достижение во вспомогательную таблицу
            # Не забыв указать к какому котику оно относится
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat)
        return cat

    # Вычисляем возраст котика.
    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year',
                  'owner', 'achievements', 'age')


class CatListSerializer(serializers.ModelSerializer):
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')


class OwnerSerializer(serializers.ModelSerializer):
    # Роль StringRelatedField — получить строковые представления связанных
    # объектов и передать их в указанное поле вместо id.

    cats = serializers.StringRelatedField(many=True, read_only=True)
    #cats = serializers.HyperlinkedRelatedField(many=True, read_only=True)

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'cats')
