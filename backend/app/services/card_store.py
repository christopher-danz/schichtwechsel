from app.models.handover import HandoverCard


class CardStore:
    def __init__(self) -> None:
        self._cards: dict[str, HandoverCard] = {}

    def save(self, card: HandoverCard) -> HandoverCard:
        self._cards[card.card_id] = card
        return card

    def get(self, card_id: str) -> HandoverCard | None:
        return self._cards.get(card_id)

    def update(self, card: HandoverCard) -> HandoverCard:
        self._cards[card.card_id] = card
        return card
