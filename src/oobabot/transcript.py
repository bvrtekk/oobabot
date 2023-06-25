# -*- coding: utf-8 -*-
"""
Stores a transcript of a voice channel.
"""
import asyncio
import datetime
import re
import typing

from oobabot import discord_utils
from oobabot import discrivener_message
from oobabot import fancy_logger
from oobabot import types


class Transcript:
    """
    Stores a transcript of a voice channel.
    """

    NUM_LINES = 300

    def __init__(
        self,
        bot_user_id: int,
        wakewords: typing.List[str],
    ):
        self._bot_user_id = bot_user_id
        self._wakewords: typing.Set[str] = set(word.lower() for word in wakewords)

        self.message_buffer = discord_utils.RingBuffer[types.VoiceMessage](
            self.NUM_LINES
        )
        self.silence_event = asyncio.Event()
        self.wakeword_event = asyncio.Event()

    def on_bot_response(self, text: str):
        """
        Adds a bot response to the transcript.
        """
        self.message_buffer.append(BotVoiceMessage(self._bot_user_id, text))

    def on_transcription(
        self,
        message: discrivener_message.UserVoiceMessage,
    ) -> None:
        self.message_buffer.append(message)

        fancy_logger.get().debug("transcript: received message: %s", message.text)

        # todo: what about wakewords which span segments?
        wakeword_found = False
        for word in re.split(r"[ .,!?\"']", message.text):
            if word.lower() in self._wakewords:
                wakeword_found = True
                break

        if wakeword_found:
            fancy_logger.get().info("transcript: wakeword detected!")
            self.wakeword_event.set()

    def on_channel_silent(
        self, activity: discrivener_message.ChannelSilentData
    ) -> None:
        if activity.silent:
            self.silence_event.set()
        else:
            self.silence_event.clear()


class BotVoiceMessage(types.VoiceMessage):
    """
    Represents a fake "transcribed" message generated by
    the bot.  This isn't a real transcription, because we got
    it from the bot, not from Discrivener.  But we're creating
    a similar object to store it in, so that we can use similar
    code to store and display it.
    """

    def __init__(
        self,
        bot_user_id: int,
        text: str,
    ):
        self._text = text
        super().__init__(
            user_id=bot_user_id,
            start_time=datetime.datetime.now(),
            duration=datetime.timedelta(seconds=1),
        )

    @property
    def text(self) -> str:
        return self._text

    @property
    def is_bot(self) -> bool:
        """
        Returns whether the user is a bot.
        """
        return True