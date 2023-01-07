import argparse
import json
import pathlib
from PIL import Image, ImageFont, ImageDraw

from pokemon_content.pokemon_elements import PokemonElements
from pokemon_content.pokemon_rarity import PokemonRarity
from mechanics.ability import Ability
from mechanics.card import Card

MONSTER_IMAGE_SCALE = 0.255
ABILITY_WIDTH = 370
ABILITY_HEIGHT = 72
ABILITY_COST_WIDTH = 76
ABILITY_COST_GAP = 12
ELEMENT_SIZE = 30
ABILITY_GAP = 4
POWER_WIDTH = 64


def render_cards(collection_path: str):
    card_path = pathlib.Path(collection_path, "cards")
    card_render_path = pathlib.Path(collection_path, "renders")
    card_render_path.mkdir(exist_ok=True)

    for card_path in card_path.iterdir():
        with open(card_path) as f:
            data = json.load(f)
            card = card_from_json(data)
            card_image = render_card(card, collection_path)
            image_name = f"{card.index:03d}_{card.snake_case_name}.png"
            card_image.save(card_render_path / f"{image_name}")


def render_card(card: Card, collection_path: str):

    card_template_name = f"{card.element.name.lower()}_card.png"
    card_image = Image.open(f"resources/cards/{card_template_name}")

    card_art_path = pathlib.Path(collection_path, "images", card.image_file)
    if pathlib.Path(card_art_path).exists():
        canvas = Image.new("RGBA", card_image.size, (0, 0, 0, 0))
        card_art_image = Image.open(card_art_path)
        resized_image_shape = (
            int(card_art_image.size[0] * MONSTER_IMAGE_SCALE),
            int(card_art_image.size[1] * MONSTER_IMAGE_SCALE),
        )
        card_art_image = card_art_image.resize(resized_image_shape)

        # Center the image.
        card_center_x = card_image.size[0] / 2
        card_center_y = 210
        monster_image_x = card_center_x - (card_art_image.size[0] / 2)
        monster_image_y = card_center_y - (card_art_image.size[1] / 2)
        canvas.paste(card_art_image, (int(monster_image_x), int(monster_image_y)))
        canvas.paste(card_image, (0, 0), card_image)
        card_image = canvas

    # Write the name of the card.
    name_text_position = (48, 64)
    title_font = ImageFont.truetype("resources/font/Cabin-Bold.ttf", 28)
    name_text = card.name

    # Draw the name text onto the card.
    draw = ImageDraw.Draw(card_image)
    draw.text(
        name_text_position, name_text, font=title_font, fill=(0, 0, 0), anchor="ls"
    )

    # Draw the HP on the card.
    hp_x_position = card_image.width - 86
    hp_y_position = 64
    hp_font = ImageFont.truetype("resources/font/Cabin_Condensed-Regular.ttf", 28)
    hp_text = f"{card.hp} HP"
    draw.text(
        (hp_x_position, hp_y_position),
        hp_text,
        font=hp_font,
        fill=(255, 0, 0),
        anchor="rs",
    )

    # Draw the abilities on the card.
    ability_y_position_center = 450
    # Center the abilities on the card.
    ability_x_position = (card_image.width - ABILITY_WIDTH) // 2

    if len(card.abilities) == 1:
        ability_y_origin = ability_y_position_center - (ABILITY_HEIGHT // 2)
    elif len(card.abilities) == 2:
        ability_y_origin = ability_y_position_center - (
            ABILITY_HEIGHT + ABILITY_COST_GAP // 2
        )

    # Draw the abilities in reverse order so that the first ability is at the bottom.
    abilities = reversed(card.abilities)
    for i, ability in enumerate(abilities):

        ability_image = render_ability(ability)
        ability_y = ability_y_origin + (i * (ABILITY_HEIGHT + ABILITY_COST_GAP))
        card_image.paste(
            ability_image,
            (int(ability_x_position), ability_y),
            ability_image,
        )

        ability_y_position_center += ABILITY_HEIGHT

    # Draw line between abilities.
    if len(card.abilities) > 1:
        # Draw line between abilities.
        line_y = ability_y_origin + ABILITY_HEIGHT
        line_extension_gap = 36
        draw.line(
            (
                (line_extension_gap, line_y),
                (card_image.width - line_extension_gap, line_y),
            ),
            fill=(0, 0, 0),
            width=2,
        )
    return card_image


def render_ability(ability: Ability):
    ability_image = Image.new("RGBA", (ABILITY_WIDTH, ABILITY_HEIGHT), (0, 0, 0, 0))
    cost_image = render_element_cost(ability.costs_as_elements)
    ability_image.paste(cost_image, (0, 0), cost_image)

    # Ability name description.
    name_text_position = (ABILITY_WIDTH // 2, ABILITY_HEIGHT // 2)
    name_font = ImageFont.truetype("resources/font/Cabin-Bold.ttf", 24)
    name_text = ability.name
    draw = ImageDraw.Draw(ability_image)
    draw.text(
        name_text_position, name_text, font=name_font, fill=(0, 0, 0), anchor="mm"
    )

    # Draw the ability power text.
    power_text_position = (ABILITY_WIDTH - 12, ABILITY_HEIGHT // 2)
    power_font = ImageFont.truetype("resources/font/Cabin_Condensed-Regular.ttf", 32)
    power_text = str(ability.power)
    draw.text(
        power_text_position,
        power_text,
        font=power_font,
        fill=(0, 0, 0),
        anchor="rm",
    )
    return ability_image


def render_element_cost(elements: list[str]):

    cost = len(elements)
    cost_canvas = Image.new(
        "RGBA", (ABILITY_COST_WIDTH, ABILITY_HEIGHT), (255, 255, 255, 0)
    )

    icon_positions = []

    # If there are two icons, they are centered and 20 pixels apart.
    # If there are three icons, they are in a triangle.
    # If there are four icons, they are in a square.

    # Work out the positions of the icons based on the number of icons.

    center_x = ABILITY_COST_WIDTH // 2
    center_y = ABILITY_HEIGHT // 2
    x_offset = center_x - (ELEMENT_SIZE // 2 + ABILITY_GAP // 2)
    x_offset_down = x_offset + ELEMENT_SIZE + ABILITY_GAP
    y_offset = center_y - (ELEMENT_SIZE + ABILITY_GAP) // 2
    y_offset_down = y_offset + ELEMENT_SIZE + ABILITY_GAP

    if cost == 1:
        # If there is only one icon, it is centered.
        icon_positions.append((center_x, center_y))
    elif cost == 2:
        icon_positions.append((x_offset, center_y))
        icon_positions.append((x_offset_down, center_y))
    elif cost == 3:
        icon_positions.append((x_offset, y_offset))
        icon_positions.append((x_offset_down, y_offset))
        icon_positions.append((center_x, y_offset_down))

    elif cost == 4:
        icon_positions.append((x_offset, y_offset))
        icon_positions.append((x_offset_down, y_offset))
        icon_positions.append((x_offset, y_offset_down))
        icon_positions.append((x_offset_down, y_offset_down))

    draw = ImageDraw.Draw(cost_canvas)
    for i, element in enumerate(elements):
        # Draw circles for each element.

        element_image = Image.open(f"resources/elements/{element.lower()}_element.png")
        element_image = element_image.resize((ELEMENT_SIZE, ELEMENT_SIZE))
        cost_canvas.paste(
            element_image,
            (
                icon_positions[i][0] - ELEMENT_SIZE // 2,
                icon_positions[i][1] - ELEMENT_SIZE // 2,
            ),
            element_image,
        )

    return cost_canvas


def card_from_json(data: dict) -> Card:
    card = Card(
        index=data["index"],
        name=data["name"],
        description=data["description"],
        element=PokemonElements.get_element_by_name(data["element"]),
        rarity=PokemonRarity.get_rarity_by_name(data["rarity"]),
        hp=data["hp"],
        part_of_evolution=data["part_of_evolution"],
    )
    card.abilities = [ability_from_json(ability) for ability in data["abilities"]]
    return card


def ability_from_json(data: dict) -> Ability:
    return Ability(
        name=data["name"],
        element=PokemonElements.get_element_by_name(data["element"]),
        cost=data["cost"],
        is_mixed_element=data["is_mixed_element"],
    )


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--collection",
        help="File path to the collection to render",
        default="data/sample_collections/standard",
    )
    collection_path = argparser.parse_args().collection
    render_cards(collection_path)


if __name__ == "__main__":
    main()