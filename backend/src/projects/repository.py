from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from base.repository import BaseRepository
from projects.models import FootageChoice, MusicRecommendation, Project, Sentence
from projects.schemas import SelectedFootage


class ProjectRepository(BaseRepository[Project]):
    """Repository for project-specific database operations."""

    def __init__(self):
        super().__init__(Project)

    async def get_by_title(self, session: AsyncSession, title: str) -> Project | None:
        """Get a project by title."""
        statement = select(self.model).where(self.model.title == title)  # type: ignore
        result = await session.execute(statement)
        return result.scalar_one_or_none()


class SentenceRepository(BaseRepository[Sentence]):
    """Repository for sentence-specific database operations."""

    def __init__(self):
        super().__init__(Sentence)

    async def get_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> list[Sentence]:
        """Get all sentences for a specific project."""
        statement = select(self.model).where(self.model.project_id == project_id)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def create_multiple(
        self,
        session: AsyncSession,
        project_id: str,
        sentences_data: list[dict[str, Any]],
    ) -> list[Sentence]:
        """Create multiple sentences for a project."""
        sentences = []
        for sentence_data in sentences_data:
            # Convert selected_footage to JSON if it exists
            selected_footage_json = None
            if (
                "selected_footage" in sentence_data
                and sentence_data["selected_footage"]
            ):
                if isinstance(sentence_data["selected_footage"], SelectedFootage):
                    selected_footage_dict = sentence_data[
                        "selected_footage"
                    ].model_dump()
                    # Convert HttpUrl to string for JSON serialization
                    if "url" in selected_footage_dict:
                        selected_footage_dict["url"] = str(selected_footage_dict["url"])
                    selected_footage_json = selected_footage_dict
                else:
                    selected_footage_json = sentence_data["selected_footage"]

            sentence_dict = {
                **sentence_data,
                "project_id": project_id,
                "selected_footage": selected_footage_json,
            }

            sentence = Sentence(**sentence_dict)
            sentences.append(sentence)
            session.add(sentence)

        await session.commit()
        for sentence in sentences:
            await session.refresh(sentence)

        return sentences

    async def update_selected_footage(
        self, session: AsyncSession, sentence_id: str, selected_footage: SelectedFootage
    ) -> Sentence | None:
        """Update the selected footage for a sentence."""
        sentence = await self.get(session, sentence_id)
        if not sentence:
            return None

        # Convert to dict and ensure HttpUrl objects are serialized as strings
        selected_footage_dict = selected_footage.model_dump()
        if "url" in selected_footage_dict:
            selected_footage_dict["url"] = str(selected_footage_dict["url"])

        sentence.selected_footage = selected_footage_dict
        await session.commit()
        await session.refresh(sentence)
        return sentence


class FootageChoiceRepository(BaseRepository[FootageChoice]):
    """Repository for footage choice-specific database operations."""

    def __init__(self):
        super().__init__(FootageChoice)

    async def get_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> list[FootageChoice]:
        """Get all footage choices for a specific project."""
        statement = select(self.model).where(self.model.project_id == project_id)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_by_sentence_id(
        self, session: AsyncSession, sentence_id: str
    ) -> FootageChoice | None:
        """Get footage choices for a specific sentence."""
        statement = select(self.model).where(self.model.sentence_id == sentence_id)  # type: ignore
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def create_multiple(
        self,
        session: AsyncSession,
        project_id: str,
        footage_choices_data: list[dict[str, Any]],
    ) -> list[FootageChoice]:
        """Create multiple footage choices for a project."""
        choices = []
        for choice_data in footage_choices_data:
            choice_dict = {**choice_data, "project_id": project_id}
            choice = FootageChoice(**choice_dict)
            choices.append(choice)
            session.add(choice)

        await session.commit()
        for choice in choices:
            await session.refresh(choice)

        return choices


class MusicRecommendationRepository(BaseRepository[MusicRecommendation]):
    """Repository for music recommendation-specific database operations."""

    def __init__(self):
        super().__init__(MusicRecommendation)

    async def get_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> list[MusicRecommendation]:
        """Get all music recommendations for a specific project."""
        statement = select(self.model).where(self.model.project_id == project_id)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def create_multiple(
        self,
        session: AsyncSession,
        project_id: str,
        recommendations_data: list[dict[str, Any]],
    ) -> list[MusicRecommendation]:
        """Create multiple music recommendations for a project."""
        recommendations = []
        for rec_data in recommendations_data:
            rec_dict = {**rec_data, "project_id": project_id}
            recommendation = MusicRecommendation(**rec_dict)
            recommendations.append(recommendation)
            session.add(recommendation)

        await session.commit()
        for recommendation in recommendations:
            await session.refresh(recommendation)

        return recommendations
