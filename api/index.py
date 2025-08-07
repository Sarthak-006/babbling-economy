from flask import Flask, request, jsonify, send_from_directory, make_response
import requests
import hashlib
import os
import time
from flask_cors import CORS
import traceback
# Import your story_nodes, other helpers (modified to remove pygame)
# MAKE SURE Pillow is installed for manga generation later
# from PIL import Image, ImageDraw # If doing manga server-side

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Constants (Remove Pygame colors/fonts) ---
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGE_MODEL = 'flux'
# ... other non-pygame constants ...
# ... your story_nodes dictionary ...

# --- Bilingual Learning Story Nodes ---
story_nodes = {
    "start": {
        "situation": "¡Hola! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
        "prompt": "Colorful classroom for kids, educational, bright colors, learning environment, child-friendly, modern classroom",
        "seed": 12345,
        "vocabulary_words": ["hola", "clase", "color", "aprender"],
        "choices": [
            {
                "text": "Look at the colorful books on the shelf",
                "next_node": "books_shelf",
                "score_modifier": 1,
                "tag": "curious",
                "vocabulary_words": ["libros", "estante", "leer", "biblioteca"]
            },
            {
                "text": "Explore the art supplies on the table",
                "next_node": "art_supplies",
                "score_modifier": 1,
                "tag": "creative",
                "vocabulary_words": ["arte", "mesa", "dibujar", "creativo"]
            },
            {
                "text": "Check out the digital learning station",
                "next_node": "digital_station",
                "score_modifier": 2,
                "tag": "tech_savvy",
                "vocabulary_words": ["computadora", "pantalla", "tecnología", "digital"]
            }
        ]
    },
    "books_shelf": {
        "situation": "You see many colorful books! There are books about animals, numbers, and colors. Which book interests you most?",
        "prompt": "Colorful children's books on shelf, educational, bright illustrations, learning materials",
        "seed": 54321,
        "vocabulary_words": ["libros", "animales", "números", "colores"],
        "choices": [
            {
                "text": "Choose the book about animals",
                "next_node": "animal_book",
                "score_modifier": 2,
                "tag": "curious",
                "vocabulary_words": ["perro", "gato", "pájaro", "pez"]
            },
            {
                "text": "Pick the book about numbers",
                "next_node": "number_book",
                "score_modifier": 2,
                "tag": "smart",
                "vocabulary_words": ["uno", "dos", "tres", "cuatro"]
            }
        ]
    },
    "animal_book": {
        "situation": "Great choice! You open the animal book and see beautiful pictures. You learn that 'perro' means dog, 'gato' means cat, and 'pájaro' means bird!",
        "prompt": "Children's book about animals, colorful illustrations, dog cat bird fish, educational",
        "seed": 67890,
        "vocabulary_words": ["perro", "gato", "pájaro", "pez", "animal"],
        "choices": [
            {
                "text": "Practice saying the animal names",
                "next_node": "practice_animals",
                "score_modifier": 2,
                "tag": "studious",
                "vocabulary_words": ["practicar", "nombres", "sonidos"]
            },
            {
                "text": "Look at more pictures in the book",
                "next_node": "more_animals",
                "score_modifier": 1,
                "tag": "curious",
                "vocabulary_words": ["más", "fotos", "bonito"]
            }
        ]
    },
    "hidden_treasure": {
        "situation": "The creature leads you to an ancient chest hidden beneath tree roots. Inside you find a magical amulet that glows with power.",
        "prompt": "Ancient treasure chest with magical glowing amulet, tree roots, fantasy forest, detailed",
        "seed": 13579,
        "choices": [
            {
                "text": "Take the amulet and wear it",
                "next_node": "amulet_power",
                "score_modifier": 2,
                "tag": "risk-taker"
            },
            {
                "text": "Leave the amulet, treasures in enchanted forests often have curses",
                "next_node": "wise_decision",
                "score_modifier": 1,
                "tag": "wise"
            }
        ]
    },
    "amulet_power": {
        "situation": "As you put on the amulet, you feel a surge of magical energy. Your senses heighten, and you can now see magical paths in the forest that were invisible before.",
        "prompt": "Character wearing glowing magical amulet, visible magical paths, enchanted forest, magical energy, detailed",
        "seed": 24680,
        "choices": [
            {
                "text": "Follow the brightest magical path",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "bold"
            },
            {
                "text": "Use your new power to find the safest way out",
                "next_node": "_calculate_end",
                "score_modifier": 0,
                "tag": "careful"
            }
        ]
    },
    "art_supplies": {
        "situation": "You see colorful paints, crayons, and paper on the table! You learn that 'pintura' means paint, 'lápices' means crayons, and 'papel' means paper.",
        "prompt": "Colorful art supplies for children, paints crayons paper, creative learning, bright colors",
        "seed": 97531,
        "vocabulary_words": ["pintura", "lápices", "papel", "colores"],
        "choices": [
            {
                "text": "Draw a picture with the supplies",
                "next_node": "drawing_activity",
                "score_modifier": 2,
                "tag": "creative",
                "vocabulary_words": ["dibujar", "imagen", "crear", "arte"]
            },
            {
                "text": "Learn the names of more colors",
                "next_node": "color_learning",
                "score_modifier": 2,
                "tag": "studious",
                "vocabulary_words": ["rojo", "azul", "verde", "amarillo"]
            }
        ]
    },
    "practice_animals": {
        "situation": "Great! You practice saying the animal names: 'perro' (dog), 'gato' (cat), 'pájaro' (bird), and 'pez' (fish). You're getting really good at pronunciation!",
        "prompt": "Child practicing pronunciation, animal flashcards, educational setting, learning environment",
        "seed": 11111,
        "vocabulary_words": ["practicar", "pronunciación", "tarjetas", "aprender"],
        "choices": [
            {
                "text": "Learn more animal names",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "studious",
                "vocabulary_words": ["más", "animales", "nombres", "nuevos"]
            },
            {
                "text": "Try counting the animals",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "smart",
                "vocabulary_words": ["contar", "uno", "dos", "tres"]
            }
        ]
    },
    "more_animals": {
        "situation": "You turn the page and see more animals! There's a 'conejo' (rabbit), 'tortuga' (turtle), 'mariposa' (butterfly), and 'abeja' (bee). So many beautiful creatures!",
        "prompt": "More animals in children's book, rabbit turtle butterfly bee, colorful illustrations, educational",
        "seed": 22222,
        "vocabulary_words": ["conejo", "tortuga", "mariposa", "abeja", "página"],
        "choices": [
            {
                "text": "Learn about animal sounds",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "curious",
                "vocabulary_words": ["sonidos", "ladrar", "maullar", "cantar"]
            },
            {
                "text": "Practice the new animal names",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "studious",
                "vocabulary_words": ["practicar", "nuevos", "nombres", "repasar"]
            }
        ]
    },
    "number_book": {
        "situation": "Excellent! You open the number book and learn to count: 'uno' (1), 'dos' (2), 'tres' (3), 'cuatro' (4), 'cinco' (5). Numbers are fun to learn!",
        "prompt": "Children's book about numbers, counting 1-5, educational illustrations, learning numbers",
        "seed": 33333,
        "vocabulary_words": ["uno", "dos", "tres", "cuatro", "cinco", "números"],
        "choices": [
            {
                "text": "Learn to count higher numbers",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "smart",
                "vocabulary_words": ["seis", "siete", "ocho", "nueve", "diez"]
            },
            {
                "text": "Practice counting objects",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "practical",
                "vocabulary_words": ["contar", "objetos", "práctica", "ejercicio"]
            }
        ]
    },
    "drawing_activity": {
        "situation": "You pick up the crayons and start drawing! You create a beautiful picture using 'rojo' (red), 'azul' (blue), 'verde' (green), and 'amarillo' (yellow). Art is so much fun!",
        "prompt": "Child drawing with crayons, colorful artwork, creative activity, art supplies, happy child",
        "seed": 44444,
        "vocabulary_words": ["dibujar", "crear", "arte", "bonito", "diversión"],
        "choices": [
            {
                "text": "Show your drawing to the teacher",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "confident",
                "vocabulary_words": ["mostrar", "maestro", "orgulloso", "trabajo"]
            },
            {
                "text": "Learn more colors for your art",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "creative",
                "vocabulary_words": ["más", "colores", "rosa", "morado", "naranja"]
            }
        ]
    },
    "color_learning": {
        "situation": "You learn more beautiful colors! 'Rosa' (pink), 'morado' (purple), 'naranja' (orange), and 'negro' (black). Now you know so many colors!",
        "prompt": "Color learning activity, pink purple orange black, educational materials, color wheel",
        "seed": 55555,
        "vocabulary_words": ["rosa", "morado", "naranja", "negro", "colores", "hermoso"],
        "choices": [
            {
                "text": "Name the colors around you",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "observant",
                "vocabulary_words": ["nombrar", "alrededor", "observar", "identificar"]
            },
            {
                "text": "Create a rainbow with all colors",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "creative",
                "vocabulary_words": ["arcoíris", "todos", "colores", "crear"]
            }
        ]
    },
    "digital_station": {
        "situation": "Wow! You discover a modern digital learning station! You learn that 'computadora' means computer, 'pantalla' means screen, and 'teclado' means keyboard. Technology is amazing!",
        "prompt": "Modern digital learning station, computer screen keyboard, educational technology, bright colors, child-friendly",
        "seed": 66666,
        "vocabulary_words": ["computadora", "pantalla", "teclado", "tecnología", "moderno"],
        "choices": [
            {
                "text": "Learn about internet and apps",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "tech_savvy",
                "vocabulary_words": ["internet", "aplicaciones", "navegar", "descargar"]
            },
            {
                "text": "Practice typing on the keyboard",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "practical",
                "vocabulary_words": ["escribir", "letras", "palabras", "práctica"]
            }
        ]
    },
    "language_expert_ending": {
        "is_end": True,
        "ending_category": "Babbling Economy Expert",
        "situation": "¡Excelente trabajo! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say hello, count numbers, name animals, describe colors, and use technology vocabulary in Spanish. Keep practicing and you'll be fluent in no time!",
        "prompt": "Happy child celebrating language learning success, educational achievement, colorful classroom, stars and confetti, modern learning",
        "seed": 11111,
        "vocabulary_words": ["excelente", "trabajo", "experto", "práctica", "economía"],
        "choices": []
    },
    "language_learner_ending": {
        "is_end": True,
        "ending_category": "Language Learner",
        "situation": "¡Buen trabajo! You've learned several new words and are making great progress in your language journey. You can now say hello and name some animals in Spanish. Keep learning and you'll become a language expert!",
        "prompt": "Child learning languages, educational progress, classroom setting, encouraging atmosphere",
        "seed": 22222,
        "vocabulary_words": ["buen", "trabajo", "progreso", "aprender"],
        "choices": []
    },
    "language_beginner_ending": {
        "is_end": True,
        "ending_category": "Language Beginner",
        "situation": "¡Bien hecho! You've taken your first steps in learning a new language. You've learned some basic words and are ready to continue your language adventure. Practice makes perfect!",
        "prompt": "Child starting language learning journey, first steps, encouraging classroom, bright future",
        "seed": 33333,
        "vocabulary_words": ["bien", "hecho", "primeros", "pasos"],
        "choices": []
    },
    "generic_neutral_ending": {
        "is_end": True,
        "ending_category": "Forest Explorer",
        "situation": "You've had an interesting adventure in the magical forest. While you didn't become a legendary hero, you've seen wonders few others have witnessed. You make your way back home, forever changed by your experiences in the enchanted woods.",
        "prompt": "Character exiting magical forest, looking back with wonder, mixed emotions, sunset, detailed",
        "seed": 22222,
        "choices": []
    },
    "generic_bad_ending": {
        "is_end": True,
        "ending_category": "Lost Wanderer",
        "situation": "Your choices have led you astray. You find yourself hopelessly lost in the darkening forest. The magical creatures no longer help you, and strange shadows follow your every move. You fear you may never find your way home again.",
        "prompt": "Lost traveler in dark fantasy forest, ominous shadows, fear, getting dark, detailed",
        "seed": 33333,
        "choices": []
    },
    "lost_forest": {
        "situation": "As you continue deeper into the forest, ignoring the trapped creature, you start to realize you're getting lost. The trees seem to close in around you.",
        "prompt": "Lost in dense fantasy forest, closing in trees, disorienting paths, foreboding atmosphere, detailed",
        "seed": 44444,
        "choices": [
            {
                "text": "Try to retrace your steps",
                "next_node": "lost_deeper",
                "score_modifier": -1,
                "tag": "practical"
            },
            {
                "text": "Climb a tree to get a better view",
                "next_node": "tree_climb",
                "score_modifier": 1,
                "tag": "resourceful"
            }
        ]
    },
    "lost_deeper": {
        "situation": "Attempting to retrace your steps only leads you deeper into the forest. Night is falling, and strange noises surround you.",
        "prompt": "Dark fantasy forest at night, eerie glowing eyes, lost traveler, fear, detailed",
        "seed": 55555,
        "choices": [
            {
                "text": "Make camp and wait for daylight",
                "next_node": "_calculate_end",
                "score_modifier": -1,
                "tag": "patient"
            },
            {
                "text": "Keep moving despite the darkness",
                "next_node": "_calculate_end",
                "score_modifier": -2,
                "tag": "stubborn"
            }
        ]
    },
    "tree_climb": {
        "situation": "From atop a tall tree, you spot a clearing with a strange stone circle that seems to glow with magic. You also see the forest edge in the far distance.",
        "prompt": "View from tall tree, fantasy forest, glowing stone circle in clearing, forest edge in distance, detailed",
        "seed": 66666,
        "choices": [
            {
                "text": "Head toward the mysterious stone circle",
                "next_node": "stone_circle",
                "score_modifier": 1,
                "tag": "curious"
            },
            {
                "text": "Make your way toward the forest edge",
                "next_node": "forest_edge",
                "score_modifier": 0,
                "tag": "cautious"
            }
        ]
    },
    "creature_guidance": {
        "situation": "The magical creature nods understandingly and offers to guide you to the forest edge instead. It leads you along a hidden path that seems to shimmer with gentle magic.",
        "prompt": "Magical creature guiding traveler along shimmering path, forest edge visible, fantasy forest, detailed",
        "seed": 77777,
        "choices": [
            {
                "text": "Thank the creature again before parting ways",
                "next_node": "forest_edge",
                "score_modifier": 1,
                "tag": "grateful"
            },
            {
                "text": "Ask the creature if it would like to accompany you further",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "friendly"
            }
        ]
    },
    "stone_circle": {
        "situation": "You find an ancient stone circle with strange symbols. The air feels charged with magic, and the stones seem to pulse with an inner light.",
        "prompt": "Ancient stone circle with glowing symbols, magical aura, fantasy forest clearing, detailed",
        "seed": 88888,
        "choices": [
            {
                "text": "Touch the central stone and speak a word of power",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "magical"
            },
            {
                "text": "Study the symbols to try to understand their meaning",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "scholarly"
            }
        ]
    },
    "wise_decision": {
        "situation": "You decide to leave the amulet behind. As you walk away, you hear a faint hissing sound and turn to see the amulet dissolving into a puddle of poisonous liquid. Your caution has saved you.",
        "prompt": "Fantasy amulet dissolving into poisonous liquid, cautious adventurer backing away, magical chest, detailed",
        "seed": 99999,
        "choices": [
            {
                "text": "Continue exploring the forest with heightened caution",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "vigilant"
            },
            {
                "text": "Ask the creature to guide you back to safer territory",
                "next_node": "creature_guidance",
                "score_modifier": 0,
                "tag": "practical"
            }
        ]
    },
    "village_arrival": {
        "situation": "You arrive at the village to find it's inhabited by friendly forest folk who welcome you warmly. They offer food and shelter, curious about your forest adventures.",
        "prompt": "Fantasy village with forest folk welcoming traveler, cozy cottages, warm lighting, detailed",
        "seed": 12121,
        "choices": [
            {
                "text": "Share your adventures and ask about the forest's secrets",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "social"
            },
            {
                "text": "Thank them but explain you need to continue your journey",
                "next_node": "_calculate_end",
                "score_modifier": 0,
                "tag": "independent"
            }
        ]
    },
    "cave_entrance": {
        "situation": "The cave entrance reveals a passage lined with glowing crystals that illuminate the darkness with a soft blue light.",
        "prompt": "Cave entrance with glowing blue crystals, mysterious passage, fantasy setting, detailed",
        "seed": 23232,
        "choices": [
            {
                "text": "Venture deeper into the crystal cave",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "brave"
            },
            {
                "text": "Take just one small crystal and head back to the forest edge",
                "next_node": "_calculate_end",
                "score_modifier": -1,
                "tag": "greedy"
            }
        ]
    },
    "heroic_savior_ending": {
        "is_end": True,
        "ending_category": "Heroic Savior",
        "situation": "Your kindness and courage have made you a legendary hero of the forest. The magical creatures see you as their champion and protector. You've discovered ancient powers within yourself that allow you to communicate with the forest and its inhabitants. Your name will be sung in the folklore of this realm for generations to come.",
        "prompt": "Epic fantasy hero, magical forest defender, ancient powers, magical creatures celebrating, detailed fantasy illustration",
        "seed": 11112,
        "choices": []
    },
    "wise_mage_ending": {
        "is_end": True,
        "ending_category": "Wise Mage",
        "situation": "Your wisdom and magical affinity have transformed you into a powerful mage. The forest has accepted you as one of its guardians, and you've established a small tower where you study the ancient magics that flow through this realm. Many travelers seek your guidance, and you've become a respected figure throughout the lands.",
        "prompt": "Wise mage in forest tower, magical tomes, arcane study, glowing runes, fantasy illustration, detailed",
        "seed": 11113,
        "choices": []
    },
    "forest_guardian_ending": {
        "is_end": True,
        "ending_category": "Forest Guardian",
        "situation": "The magic of the forest has chosen you as its guardian. You've bonded with the ancient spirits of the woods, gaining the ability to shape and protect this magical realm. Your body now carries marks of the forest—perhaps leaves for hair or bark-like skin—as you've become part-human, part-forest entity, respected and sometimes feared by those who enter your domain.",
        "prompt": "Human-forest hybrid guardian, bark skin, leaf hair, forest spirits, magical forest throne, fantasy character, detailed illustration",
        "seed": 11114,
        "choices": []
    },
    "peaceful_traveler_ending": {
        "is_end": True,
        "ending_category": "Peaceful Traveler",
        "situation": "You've explored the wonders of the magical forest and learned much from your journey. Though you didn't become a legendary hero, you carry the forest's wisdom with you. You now travel between villages, sharing tales of the enchanted woods and occasionally using small magics you learned there to help those in need.",
        "prompt": "Wandering storyteller, magical trinkets, village gathering, fantasy traveler, sunset, detailed illustration",
        "seed": 22223,
        "choices": []
    },
    "forest_explorer_ending": {
        "is_end": True, 
        "ending_category": "Forest Explorer",
        "situation": "Your exploration of the magical forest has made you a renowned expert in magical flora and fauna. You've documented countless species unknown to the outside world, creating detailed journals that scholars pay handsomely to study. You now lead occasional expeditions into the forest, guiding those brave enough to witness its wonders.",
        "prompt": "Fantasy naturalist, magical creature sketches, expedition camp, journals, forest background, detailed illustration",
        "seed": 22224,
        "choices": []
    },
    "merchant_ending": {
        "is_end": True,
        "ending_category": "Forest Merchant",
        "situation": "Your adventures in the magical forest have given you access to rare herbs, magical trinkets, and exotic materials. You've established a small but profitable trading post at the forest's edge, becoming the go-to merchant for magical components. Wizards and alchemists from far and wide seek your uniquely sourced goods.",
        "prompt": "Fantasy merchant shop, magical herbs and potions, trading post, forest edge, customer wizards, detailed illustration",
        "seed": 22225,
        "choices": []
    },
    "lost_soul_ending": {
        "is_end": True,
        "ending_category": "Lost Soul",
        "situation": "The forest's magic has clouded your mind and you've lost your way—both literally and figuratively. You wander the ever-shifting paths, no longer remembering who you were before entering these woods. The forest creatures watch you with pity, but none approach, for you have become a cautionary tale told to those who might enter the forest unprepared.",
        "prompt": "Lost wanderer in dark forest, tattered clothes, confused expression, glowing eyes watching from darkness, fantasy horror, detailed illustration",
        "seed": 33334,
        "choices": []
    },
    "cursed_wanderer_ending": {
        "is_end": True,
        "ending_category": "Cursed Wanderer",
        "situation": "Your selfish actions in the forest have drawn the ire of ancient spirits. A curse now follows you—perhaps your shadow moves independently, or your reflection shows a twisted version of yourself. You search endlessly for a cure, but the curse seems to strengthen the further you get from the forest that birthed it.",
        "prompt": "Cursed traveler, unnatural shadow, twisted reflection in water, dark fantasy, horror elements, detailed illustration",
        "seed": 33335,
        "choices": []
    },
    "forest_prisoner_ending": {
        "is_end": True,
        "ending_category": "Forest Prisoner",
        "situation": "The forest has claimed you as its prisoner. The paths continuously lead you back to the center, no matter which direction you travel. You've built a small shelter and learned to survive, but freedom eludes you. Sometimes you see other travelers through the trees, but when you call out, they cannot seem to hear you—as if you exist in a separate layer of reality.",
        "prompt": "Prisoner of magical forest, small shelter, paths that loop back, barrier of light, travelers passing by unaware, fantasy horror, detailed illustration",
        "seed": 33336,
        "choices": []
    }
}

# --- Game State (In-memory - BAD for multiple users/production) ---
game_state = {
    "current_node_id": "start",
    "story_path": [], # Store tuples: (node_id, choice_text, score_mod)
    "current_score": 0,
    "sentiment_tally": {},
    "last_error": None,
    "last_reset": time.time()  # Track when the game was last reset
}

# Add a user_sessions dictionary to track individual user sessions
user_sessions = {}

# --- Helper Functions (Refactored - NO PYGAME) ---
def get_dynamic_seed(base_seed, path_node_ids, session_id=None):
    """Generate a unique seed based on the path taken and session ID"""
    if not session_id:
        # Use existing path-based seed if no session ID
        path_hash = hashlib.md5(''.join(path_node_ids).encode()).hexdigest()
        seed = (base_seed + int(path_hash, 16)) % 999999
    else:
        # Create a unique seed combining base seed, path, and session ID
        combined = f"{base_seed}-{''.join(path_node_ids)}-{session_id}"
        seed_hash = hashlib.md5(combined.encode()).hexdigest()
        seed = int(seed_hash, 16) % 999999
    
    return seed

def enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id=None):
    """Enhance the base prompt with unique elements based on the user's journey"""
    # Get the user's style preferences (if stored in their session)
    style_elements = []
    if session_id and session_id in user_sessions and 'style_preferences' in user_sessions[session_id]:
        style_elements = user_sessions[session_id]['style_preferences']
    
    # Default style elements if none are set
    if not style_elements:
        style_elements = ["detailed", "fantasy", "ethereal"]
    
    # Add sentiment-based modifiers
    if sentiment_tally.get('kind', 0) > sentiment_tally.get('selfish', 0):
        style_elements.append("warm light")
    else:
        style_elements.append("cool tones")
        
    if sentiment_tally.get('adventurous', 0) > 1:
        style_elements.append("vibrant")
    
    if sentiment_tally.get('cautious', 0) > 1:
        style_elements.append("muted colors")
    
    # Add a unique element based on session ID if available
    if session_id:
        # Use the session ID to deterministically select unique style elements
        session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        
        # List of potential style modifiers to make images unique
        unique_styles = [
            "cinematic lighting", "golden hour", "blue hour", "mist", 
            "ray tracing", "dramatic shadows", "soft focus", "high contrast",
            "low saturation", "high saturation", "dreamlike", "surreal",
            "watercolor style", "oil painting style", "concept art", "digital art"
        ]
        
        # Select 1-3 unique styles based on session ID
        num_styles = 1 + (session_hash % 3)  # 1 to 3 styles
        for i in range(num_styles):
            style_index = (session_hash + i) % len(unique_styles)
            style_elements.append(unique_styles[style_index])
    
    # Combine everything into an enhanced prompt
    enhanced = f"{base_prompt}, {', '.join(style_elements)}"
    
    # Make each image different even for the same node by adding timestamp
    timestamp = int(time.time())
    enhanced += f", seed:{timestamp}"
    
    return enhanced

def reset_game_state(session_id=None):
    """Reset the game state"""
    initial_state = {
        "current_node_id": "start",
        "path_history": ["start"],
        "score": 0,
        "sentiment_tally": {},
        "choice_history": [],
        "created_at": time.time()
    }
    
    # If we have a session ID, store the state in the user_sessions dictionary
    if session_id:
        if session_id not in user_sessions:
            user_sessions[session_id] = {}
        
        # Generate some random style preferences for this session
        import random
        all_style_options = [
            "fantasy", "medieval", "ethereal", "mystical", "dramatic", 
            "whimsical", "dark", "bright", "colorful", "muted"
        ]
        user_sessions[session_id]['style_preferences'] = random.sample(all_style_options, 3)
        user_sessions[session_id]['state'] = initial_state
        return user_sessions[session_id]['state']
    
    return initial_state

def get_node_details(node_id, language='es'):
    """Get details for a story node with personalized content and language support"""
    try:
        # Get base node
        node = story_nodes.get(node_id)
        if not node:
            return None
            
        # Make a copy so we don't modify the original
        node_copy = node.copy()
        
        # Add language-specific translations and vocabulary
        if language == 'es':
            # Spanish is the default, no translation needed
            node_copy["translation"] = ""
        elif language == 'ja':
            # Japanese - Show Japanese text as main situation, English as translation
            japanese_translations = {
                "start": "Hello! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about animals, numbers, and colors. Which book interests you most?",
                "animal_book": "Great choice! You open the animal book and see beautiful pictures. You learn that 'dog' means 犬, 'cat' means 猫, and 'bird' means 鳥!",
                "practice_animals": "Great! You practice the animal names: 'dog' (犬), 'cat' (猫), 'bird' (鳥), and 'fish' (魚). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'rabbit' (ウサギ), 'turtle' (カメ), 'butterfly' (蝶), and 'bee' (蜂). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'one' (一), 'two' (二), 'three' (三), 'four' (四), 'five' (五). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'paint' means 絵の具, 'crayons' means クレヨン, and 'paper' means 紙.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'red' (赤), 'blue' (青), 'green' (緑), and 'yellow' (黄). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Pink' (ピンク), 'purple' (紫), 'orange' (オレンジ), and 'black' (黒). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'computer' means コンピューター, 'screen' means 画面, and 'keyboard' means キーボード. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say hello, count numbers, name animals, describe colors, and use technology vocabulary in Japanese. Keep practicing and you'll be bilingual in no time!"
            }
            # Set the main situation text to Japanese and translation to English
            translations = {
                "start": "こんにちは！バブリングエコノミーの冒険へようこそ！あなたは色とりどりの教室にいて、周りには興味深いものがたくさんあります。学習を始めましょう！",
                "books_shelf": "カラフルな本がたくさん見えます！動物、数字、色についての本があります。どの本が一番興味深いですか？",
                "animal_book": "素晴らしい選択です！動物の本を開いて美しい絵を見ます。'犬'はdog、'猫'はcat、'鳥'はbirdということを学びます！",
                "practice_animals": "素晴らしい！動物の名前を練習します：'犬'（dog）、'猫'（cat）、'鳥'（bird）、'魚'（fish）。発音が本当に上手になっています！",
                "more_animals": "ページをめくると、もっと多くの動物が見えます！'ウサギ'（rabbit）、'カメ'（turtle）、'蝶'（butterfly）、'蜂'（bee）がいます。美しい生き物がたくさんいますね！",
                "number_book": "素晴らしい！数字の本を開いて数え方を学びます：'一'（1）、'二'（2）、'三'（3）、'四'（4）、'五'（5）。数字を学ぶのは楽しいです！",
                "art_supplies": "テーブルの上にカラフルな絵の具、クレヨン、紙が見えます！'絵の具'はpaint、'クレヨン'はcrayons、'紙'はpaperということを学びます。",
                "drawing_activity": "クレヨンを手に取って絵を描き始めます！'赤'（red）、'青'（blue）、'緑'（green）、'黄'（yellow）を使って美しい絵を作ります。アートは本当に楽しいです！",
                "color_learning": "もっと多くの美しい色を学びます！'ピンク'（pink）、'紫'（purple）、'オレンジ'（orange）、'黒'（black）。今は多くの色を知っています！",
                "digital_station": "わあ！現代的なデジタル学習ステーションを発見しました！'コンピューター'はcomputer、'画面'はscreen、'キーボード'はkeyboardということを学びます。テクノロジーは素晴らしいです！",
                "language_expert_ending": "素晴らしい仕事です！バブリングエコノミーで多くの新しい単語を学び、言語の専門家になっています！今はこんにちはと言い、数字を数え、動物の名前を言い、色を説明し、日本語でテクノロジーの語彙を使うことができます。練習を続ければ、すぐにバイリンガルになります！"
            }
            node_copy["situation"] = translations.get(node_id, node_copy["situation"])
            node_copy["translation"] = japanese_translations.get(node_id, "")
        elif language == 'fr':
            # French - English text with French vocabulary
            translations = {
                "start": "Bonjour! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about 'animaux' (animals), 'nombres' (numbers), and 'couleurs' (colors). Which book interests you most?",
                "animal_book": "Excellent choice! You open the animal book and see beautiful pictures. You learn that 'chien' means dog, 'chat' means cat, and 'oiseau' means bird!",
                "practice_animals": "Perfect! You practice the animal names: 'chien' (dog), 'chat' (cat), 'oiseau' (bird), and 'poisson' (fish). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'lapin' (rabbit), 'tortue' (turtle), 'papillon' (butterfly), and 'abeille' (bee). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'un' (1), 'deux' (2), 'trois' (3), 'quatre' (4), 'cinq' (5). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'peinture' means paint, 'crayons' means crayons, and 'papier' means paper.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'rouge' (red), 'bleu' (blue), 'vert' (green), and 'jaune' (yellow). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Rose' (pink), 'violet' (purple), 'orange' (orange), and 'noir' (black). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'ordinateur' means computer, 'écran' means screen, and 'clavier' means keyboard. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say bonjour, count numbers, name animals, describe colors, and use technology vocabulary in French. Keep practicing and you'll be bilingual in no time!"
            }
            node_copy["translation"] = translations.get(node_id, "")
            # Update vocabulary words for French
            if node_copy.get("vocabulary_words"):
                french_vocab = {
                    "start": ["bonjour", "classe", "couleur", "apprendre"],
                    "books_shelf": ["livres", "étagère", "lire", "bibliothèque"],
                    "animal_book": ["chien", "chat", "oiseau", "poisson", "animal"],
                    "practice_animals": ["pratiquer", "prononciation", "cartes", "apprendre"],
                    "more_animals": ["lapin", "tortue", "papillon", "abeille", "page"],
                    "number_book": ["un", "deux", "trois", "quatre", "cinq", "nombres"],
                    "art_supplies": ["peinture", "crayons", "papier", "couleurs"],
                    "drawing_activity": ["dessiner", "créer", "art", "beau", "amusement"],
                    "color_learning": ["rose", "violet", "orange", "noir", "couleurs", "beau"],
                    "digital_station": ["ordinateur", "écran", "clavier", "technologie", "moderne"]
                }
                node_copy["vocabulary_words"] = french_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'de':
            # German - English text with German vocabulary
            translations = {
                "start": "Hallo! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about 'Tiere' (animals), 'Zahlen' (numbers), and 'Farben' (colors). Which book interests you most?",
                "animal_book": "Great choice! You open the animal book and see beautiful pictures. You learn that 'Hund' means dog, 'Katze' means cat, and 'Vogel' means bird!",
                "practice_animals": "Great! You practice the animal names: 'Hund' (dog), 'Katze' (cat), 'Vogel' (bird), and 'Fisch' (fish). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'Hase' (rabbit), 'Schildkröte' (turtle), 'Schmetterling' (butterfly), and 'Biene' (bee). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'eins' (1), 'zwei' (2), 'drei' (3), 'vier' (4), 'fünf' (5). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'Farbe' means paint, 'Buntstifte' means crayons, and 'Papier' means paper.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'rot' (red), 'blau' (blue), 'grün' (green), and 'gelb' (yellow). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Rosa' (pink), 'lila' (purple), 'orange' (orange), and 'schwarz' (black). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'Computer' means computer, 'Bildschirm' means screen, and 'Tastatur' means keyboard. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say hallo, count numbers, name animals, describe colors, and use technology vocabulary in German. Keep practicing and you'll be bilingual in no time!"
            }
            node_copy["translation"] = translations.get(node_id, "")
            # Update vocabulary words for German
            if node_copy.get("vocabulary_words"):
                german_vocab = {
                    "start": ["hallo", "klasse", "farbe", "lernen"],
                    "books_shelf": ["bücher", "regal", "lesen", "bibliothek"],
                    "animal_book": ["hund", "katze", "vogel", "fisch", "tier"],
                    "practice_animals": ["üben", "aussprache", "karten", "lernen"],
                    "more_animals": ["hase", "schildkröte", "schmetterling", "biene", "seite"],
                    "number_book": ["eins", "zwei", "drei", "vier", "fünf", "zahlen"],
                    "art_supplies": ["farbe", "buntstifte", "papier", "farben"],
                    "drawing_activity": ["zeichnen", "erstellen", "kunst", "schön", "spaß"],
                    "color_learning": ["rosa", "lila", "orange", "schwarz", "farben", "schön"],
                    "digital_station": ["computer", "bildschirm", "tastatur", "technologie", "modern"]
                }
                node_copy["vocabulary_words"] = german_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'it':
            # Italian - English text with Italian vocabulary
            translations = {
                "start": "Ciao! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about 'animali' (animals), 'numeri' (numbers), and 'colori' (colors). Which book interests you most?",
                "animal_book": "Great choice! You open the animal book and see beautiful pictures. You learn that 'cane' means dog, 'gatto' means cat, and 'uccello' means bird!",
                "practice_animals": "Perfect! You practice the animal names: 'cane' (dog), 'gatto' (cat), 'uccello' (bird), and 'pesce' (fish). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'coniglio' (rabbit), 'tartaruga' (turtle), 'farfalla' (butterfly), and 'ape' (bee). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'uno' (1), 'due' (2), 'tre' (3), 'quattro' (4), 'cinque' (5). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'pittura' means paint, 'pastelli' means crayons, and 'carta' means paper.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'rosso' (red), 'blu' (blue), 'verde' (green), and 'giallo' (yellow). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Rosa' (pink), 'viola' (purple), 'arancione' (orange), and 'nero' (black). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'computer' means computer, 'schermo' means screen, and 'tastiera' means keyboard. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say ciao, count numbers, name animals, describe colors, and use technology vocabulary in Italian. Keep practicing and you'll be bilingual in no time!"
            }
            node_copy["translation"] = translations.get(node_id, "")
            # Update vocabulary words for Italian
            if node_copy.get("vocabulary_words"):
                italian_vocab = {
                    "start": ["ciao", "classe", "colore", "imparare"],
                    "books_shelf": ["libri", "scaffale", "leggere", "biblioteca"],
                    "animal_book": ["cane", "gatto", "uccello", "pesce", "animale"],
                    "practice_animals": ["praticare", "pronuncia", "carte", "imparare"],
                    "more_animals": ["coniglio", "tartaruga", "farfalla", "ape", "pagina"],
                    "number_book": ["uno", "due", "tre", "quattro", "cinque", "numeri"],
                    "art_supplies": ["pittura", "pastelli", "carta", "colori"],
                    "drawing_activity": ["disegnare", "creare", "arte", "bello", "divertimento"],
                    "color_learning": ["rosa", "viola", "arancione", "nero", "colori", "bello"],
                    "digital_station": ["computer", "schermo", "tastiera", "tecnologia", "moderno"]
                }
                node_copy["vocabulary_words"] = italian_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'pt':
            # Portuguese - English text with Portuguese vocabulary
            translations = {
                "start": "Olá! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about 'animais' (animals), 'números' (numbers), and 'cores' (colors). Which book interests you most?",
                "animal_book": "Excellent choice! You open the animal book and see beautiful pictures. You learn that 'cão' means dog, 'gato' means cat, and 'pássaro' means bird!",
                "practice_animals": "Perfect! You practice the animal names: 'cão' (dog), 'gato' (cat), 'pássaro' (bird), and 'peixe' (fish). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'coelho' (rabbit), 'tartaruga' (turtle), 'borboleta' (butterfly), and 'abelha' (bee). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'um' (1), 'dois' (2), 'três' (3), 'quatro' (4), 'cinco' (5). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'tinta' means paint, 'lápis' means crayons, and 'papel' means paper.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'vermelho' (red), 'azul' (blue), 'verde' (green), and 'amarelo' (yellow). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Rosa' (pink), 'roxo' (purple), 'laranja' (orange), and 'preto' (black). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'computador' means computer, 'tela' means screen, and 'teclado' means keyboard. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say olá, count numbers, name animals, describe colors, and use technology vocabulary in Portuguese. Keep practicing and you'll be bilingual in no time!"
            }
            node_copy["translation"] = translations.get(node_id, "")
            # Update vocabulary words for Portuguese
            if node_copy.get("vocabulary_words"):
                portuguese_vocab = {
                    "start": ["olá", "classe", "cor", "aprender"],
                    "books_shelf": ["livros", "prateleira", "ler", "biblioteca"],
                    "animal_book": ["cão", "gato", "pássaro", "peixe", "animal"],
                    "practice_animals": ["praticar", "pronúncia", "cartões", "aprender"],
                    "more_animals": ["coelho", "tartaruga", "borboleta", "abelha", "página"],
                    "number_book": ["um", "dois", "três", "quatro", "cinco", "números"],
                    "art_supplies": ["tinta", "lápis", "papel", "cores"],
                    "drawing_activity": ["desenhar", "criar", "arte", "bonito", "diversão"],
                    "color_learning": ["rosa", "roxo", "laranja", "preto", "cores", "bonito"],
                    "digital_station": ["computador", "tela", "teclado", "tecnologia", "moderno"]
                }
                node_copy["vocabulary_words"] = portuguese_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'ja':
            # Japanese - Full Japanese text with English translations
            translations = {
                "start": "こんにちは！バブリングエコノミーの冒険へようこそ！あなたは色とりどりの教室にいて、周りには興味深いものがたくさんあります。学習を始めましょう！",
                "books_shelf": "カラフルな本がたくさん見えます！動物、数字、色についての本があります。どの本が一番興味深いですか？",
                "animal_book": "素晴らしい選択です！動物の本を開いて美しい絵を見ます。'犬'はdog、'猫'はcat、'鳥'はbirdということを学びます！",
                "practice_animals": "素晴らしい！動物の名前を練習します：'犬'（dog）、'猫'（cat）、'鳥'（bird）、'魚'（fish）。発音が本当に上手になっています！",
                "more_animals": "ページをめくると、もっと多くの動物が見えます！'ウサギ'（rabbit）、'カメ'（turtle）、'蝶'（butterfly）、'蜂'（bee）がいます。美しい生き物がたくさんいますね！",
                "number_book": "素晴らしい！数字の本を開いて数え方を学びます：'一'（1）、'二'（2）、'三'（3）、'四'（4）、'五'（5）。数字を学ぶのは楽しいです！",
                "art_supplies": "テーブルの上にカラフルな絵の具、クレヨン、紙が見えます！'絵の具'はpaint、'クレヨン'はcrayons、'紙'はpaperということを学びます。",
                "drawing_activity": "クレヨンを手に取って絵を描き始めます！'赤'（red）、'青'（blue）、'緑'（green）、'黄'（yellow）を使って美しい絵を作ります。アートは本当に楽しいです！",
                "color_learning": "もっと多くの美しい色を学びます！'ピンク'（pink）、'紫'（purple）、'オレンジ'（orange）、'黒'（black）。今は多くの色を知っています！",
                "digital_station": "わあ！現代的なデジタル学習ステーションを発見しました！'コンピューター'はcomputer、'画面'はscreen、'キーボード'はkeyboardということを学びます。テクノロジーは素晴らしいです！",
                "language_expert_ending": "素晴らしい仕事です！バブリングエコノミーで多くの新しい単語を学び、言語の専門家になっています！今はこんにちはと言い、数字を数え、動物の名前を言い、色を説明し、日本語でテクノロジーの語彙を使うことができます。練習を続ければ、すぐにバイリンガルになります！"
            }
            # Update vocabulary words for Japanese
            if node_copy.get("vocabulary_words"):
                japanese_vocab = {
                    "start": ["こんにちは", "クラス", "色", "学ぶ"],
                    "books_shelf": ["本", "棚", "読む", "図書館"],
                    "animal_book": ["犬", "猫", "鳥", "魚", "動物"],
                    "practice_animals": ["練習", "発音", "カード", "学ぶ"],
                    "more_animals": ["ウサギ", "カメ", "蝶", "蜂", "ページ"],
                    "number_book": ["一", "二", "三", "四", "五", "数字"],
                    "art_supplies": ["絵の具", "クレヨン", "紙", "色"],
                    "drawing_activity": ["描く", "作る", "アート", "美しい", "楽しい"],
                    "color_learning": ["ピンク", "紫", "オレンジ", "黒", "色", "美しい"],
                    "digital_station": ["コンピューター", "画面", "キーボード", "テクノロジー", "モダン"]
                }
                node_copy["vocabulary_words"] = japanese_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'ko':
            # Korean - Show Korean text as main situation, English as translation
            korean_translations = {
                "start": "Hello! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about animals, numbers, and colors. Which book interests you most?",
                "animal_book": "Great choice! You open the animal book and see beautiful pictures. You learn that 'dog' means 개, 'cat' means 고양이, and 'bird' means 새!",
                "practice_animals": "Great! You practice the animal names: 'dog' (개), 'cat' (고양이), 'bird' (새), and 'fish' (물고기). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'rabbit' (토끼), 'turtle' (거북), 'butterfly' (나비), and 'bee' (벌). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'one' (하나), 'two' (둘), 'three' (셋), 'four' (넷), 'five' (다섯). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'paint' means 페인트, 'crayons' means 크레용, and 'paper' means 종이.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'red' (빨간색), 'blue' (파란색), 'green' (초록색), and 'yellow' (노란색). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Pink' (분홍색), 'purple' (보라색), 'orange' (주황색), and 'black' (검은색). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'computer' means 컴퓨터, 'screen' means 화면, and 'keyboard' means 키보드. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say hello, count numbers, name animals, describe colors, and use technology vocabulary in Korean. Keep practicing and you'll be bilingual in no time!"
            }
            # Set the main situation text to Korean and translation to English
            translations = {
                "start": "안녕하세요! 바블링 이코노미 모험에 오신 것을 환영합니다! 당신은 주변에 흥미로운 물건들이 많은 다채로운 교실에 있습니다. 학습을 시작해 봅시다!",
                "books_shelf": "컬러풀한 책들이 많이 보입니다! 동물, 숫자, 색깔에 대한 책들이 있습니다. 어떤 책이 가장 흥미롭나요?",
                "animal_book": "훌륭한 선택입니다! 동물 책을 열고 아름다운 그림들을 봅니다. '개'는 dog, '고양이'는 cat, '새'는 bird라는 것을 배웁니다!",
                "practice_animals": "훌륭합니다! 동물 이름들을 연습합니다: '개' (dog), '고양이' (cat), '새' (bird), '물고기' (fish). 발음이 정말 좋아지고 있습니다!",
                "more_animals": "페이지를 넘기면 더 많은 동물들이 보입니다! '토끼' (rabbit), '거북' (turtle), '나비' (butterfly), '벌' (bee)이 있습니다. 아름다운 생물들이 많네요!",
                "number_book": "훌륭합니다! 숫자 책을 열고 세는 법을 배웁니다: '하나' (1), '둘' (2), '셋' (3), '넷' (4), '다섯' (5). 숫자를 배우는 것은 재미있습니다!",
                "art_supplies": "테이블 위에 컬러풀한 페인트, 크레용, 종이가 보입니다! '페인트'는 paint, '크레용'은 crayons, '종이'는 paper라는 것을 배웁니다.",
                "drawing_activity": "크레용을 들고 그림을 그리기 시작합니다! '빨간색' (red), '파란색' (blue), '초록색' (green), '노란색' (yellow)을 사용해서 아름다운 그림을 만듭니다. 예술은 정말 재미있습니다!",
                "color_learning": "더 많은 아름다운 색깔들을 배웁니다! '분홍색' (pink), '보라색' (purple), '주황색' (orange), '검은색' (black). 이제 많은 색깔들을 알고 있습니다!",
                "digital_station": "와! 현대적인 디지털 학습 스테이션을 발견했습니다! '컴퓨터'는 computer, '화면'은 screen, '키보드'는 keyboard라는 것을 배웁니다. 기술은 놀랍습니다!",
                "language_expert_ending": "훌륭한 작업입니다! 바블링 이코노미에서 많은 새로운 단어들을 배우고 언어 전문가가 되고 있습니다! 이제 안녕하세요라고 말하고, 숫자를 세고, 동물 이름을 말하고, 색깔을 설명하고, 한국어로 기술 어휘를 사용할 수 있습니다. 연습을 계속하면 곧 이중 언어자가 될 것입니다!"
            }
            node_copy["situation"] = translations.get(node_id, node_copy["situation"])
            node_copy["translation"] = korean_translations.get(node_id, "")
            # Update vocabulary words for Korean
            if node_copy.get("vocabulary_words"):
                korean_vocab = {
                    "start": ["안녕하세요", "교실", "색깔", "배우다"],
                    "books_shelf": ["책", "선반", "읽다", "도서관"],
                    "animal_book": ["개", "고양이", "새", "물고기", "동물"],
                    "practice_animals": ["연습", "발음", "카드", "배우다"],
                    "more_animals": ["토끼", "거북", "나비", "벌", "페이지"],
                    "number_book": ["하나", "둘", "셋", "넷", "다섯", "숫자"],
                    "art_supplies": ["페인트", "크레용", "종이", "색깔"],
                    "drawing_activity": ["그리다", "만들다", "예술", "아름답다", "재미있다"],
                    "color_learning": ["분홍색", "보라색", "주황색", "검은색", "색깔", "아름답다"],
                    "digital_station": ["컴퓨터", "화면", "키보드", "기술", "현대적"]
                }
                node_copy["vocabulary_words"] = korean_vocab.get(node_id, node_copy["vocabulary_words"])
        elif language == 'zh':
            # Chinese - Show Chinese text as main situation, English as translation
            chinese_translations = {
                "start": "Hello! Welcome to your Babbling Economy adventure! You're in a colorful classroom with many interesting objects around you. Let's start learning!",
                "books_shelf": "You see many colorful books! There are books about animals, numbers, and colors. Which book interests you most?",
                "animal_book": "Great choice! You open the animal book and see beautiful pictures. You learn that 'dog' means 狗, 'cat' means 猫, and 'bird' means 鸟!",
                "practice_animals": "Great! You practice the animal names: 'dog' (狗), 'cat' (猫), 'bird' (鸟), and 'fish' (鱼). You're getting really good at pronunciation!",
                "more_animals": "You turn the page and see more animals! There's a 'rabbit' (兔子), 'turtle' (乌龟), 'butterfly' (蝴蝶), and 'bee' (蜜蜂). So many beautiful creatures!",
                "number_book": "Excellent! You open the number book and learn to count: 'one' (一), 'two' (二), 'three' (三), 'four' (四), 'five' (五). Numbers are fun to learn!",
                "art_supplies": "You see colorful paints, crayons, and paper on the table! You learn that 'paint' means 颜料, 'crayons' means 蜡笔, and 'paper' means 纸.",
                "drawing_activity": "You pick up the crayons and start drawing! You create a beautiful picture using 'red' (红色), 'blue' (蓝色), 'green' (绿色), and 'yellow' (黄色). Art is so much fun!",
                "color_learning": "You learn more beautiful colors! 'Pink' (粉色), 'purple' (紫色), 'orange' (橙色), and 'black' (黑色). Now you know so many colors!",
                "digital_station": "Wow! You discover a modern digital learning station! You learn that 'computer' means 电脑, 'screen' means 屏幕, and 'keyboard' means 键盘. Technology is amazing!",
                "language_expert_ending": "Excellent work! You've learned so many new words and are becoming a language expert in the Babbling Economy! You can now say hello, count numbers, name animals, describe colors, and use technology vocabulary in Chinese. Keep practicing and you'll be bilingual in no time!"
            }
            # Set the main situation text to Chinese and translation to English
            translations = {
                "start": "你好！欢迎来到你的巴布林经济冒险！你在一个色彩缤纷的教室里，周围有很多有趣的东西。让我们开始学习吧！",
                "books_shelf": "你看到很多彩色书籍！有关于动物、数字和颜色的书。哪本书最让你感兴趣？",
                "animal_book": "很好的选择！你打开动物书看到美丽的图片。你学到'狗'是dog，'猫'是cat，'鸟'是bird！",
                "practice_animals": "太棒了！你练习动物名称：'狗'（dog），'猫'（cat），'鸟'（bird），'鱼'（fish）。你的发音真的在进步！",
                "more_animals": "你翻页看到更多动物！有'兔子'（rabbit），'乌龟'（turtle），'蝴蝶'（butterfly），'蜜蜂'（bee）。这么多美丽的生物！",
                "number_book": "太好了！你打开数字书学习数数：'一'（1），'二'（2），'三'（3），'四'（4），'五'（5）。学习数字很有趣！",
                "art_supplies": "你看到桌上有彩色颜料、蜡笔和纸！你学到'颜料'是paint，'蜡笔'是crayons，'纸'是paper。",
                "drawing_activity": "你拿起蜡笔开始画画！你用'红色'（red），'蓝色'（blue），'绿色'（green），'黄色'（yellow）创作美丽的图画。艺术真有趣！",
                "color_learning": "你学习更多美丽的颜色！'粉色'（pink），'紫色'（purple），'橙色'（orange），'黑色'（black）。现在你知道这么多颜色了！",
                "digital_station": "哇！你发现了一个现代数字学习站！你学到'电脑'是computer，'屏幕'是screen，'键盘'是keyboard。科技真神奇！",
                "language_expert_ending": "出色的工作！你在巴布林经济中学到了很多新单词，正在成为语言专家！现在你可以说你好、数数、说出动物名称、描述颜色并用中文使用技术词汇。继续练习，你很快就会成为双语者！"
            }
            node_copy["situation"] = translations.get(node_id, node_copy["situation"])
            node_copy["translation"] = chinese_translations.get(node_id, "")
            # Update vocabulary words for Chinese
            if node_copy.get("vocabulary_words"):
                chinese_vocab = {
                    "start": ["你好", "教室", "颜色", "学习"],
                    "books_shelf": ["书", "书架", "读", "图书馆"],
                    "animal_book": ["狗", "猫", "鸟", "鱼", "动物"],
                    "practice_animals": ["练习", "发音", "卡片", "学习"],
                    "more_animals": ["兔子", "乌龟", "蝴蝶", "蜜蜂", "页面"],
                    "number_book": ["一", "二", "三", "四", "五", "数字"],
                    "art_supplies": ["颜料", "蜡笔", "纸", "颜色"],
                    "drawing_activity": ["画", "创造", "艺术", "美丽", "有趣"],
                    "color_learning": ["粉色", "紫色", "橙色", "黑色", "颜色", "美丽"],
                    "digital_station": ["电脑", "屏幕", "键盘", "科技", "现代"]
                }
                node_copy["vocabulary_words"] = chinese_vocab.get(node_id, node_copy["vocabulary_words"])
        
        # Personalize choices if we're not at an end node
        if not node_copy.get("is_end", False) and "choices" in node_copy:
            # Deep copy choices to avoid modifying original
            node_copy["choices"] = [choice.copy() for choice in node_copy["choices"]]
            
            # Personalize choice texts with small variations
            for choice in node_copy["choices"]:
                if "text" in choice:
                    # We could add small variations to choice text here
                    # But we'll keep the first choice consistent as required
                    pass  # Implemented in the next update
        
        return node_copy
        
    except Exception as e:
        traceback.print_exc()
        return None

# --- API Endpoints ---
@app.route('/')
def serve_index():
    try:
        return send_from_directory('../public', 'index.html')
    except Exception as e:
        print(f"Error serving index: {str(e)}")
        return f"Error serving page: {str(e)}", 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('../public', path)
    except Exception as e:
        print(f"Error serving static file {path}: {str(e)}")
        return f"Error serving file: {str(e)}", 404

@app.route('/api/state', methods=['GET'])
def get_current_state():
    try:
        # Get language parameter
        language = request.args.get('language', 'es')
        
        # Get user's session ID from cookies or create a new one
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            session_id = hashlib.md5(f"{time.time()}-{os.urandom(8).hex()}".encode()).hexdigest()
        
        # Get or create the user's game state
        if session_id in user_sessions and 'state' in user_sessions[session_id]:
            game_state = user_sessions[session_id]['state']
        else:
            game_state = reset_game_state(session_id)
        
        current_node_id = game_state["current_node_id"]
        node_details = get_node_details(current_node_id, language)
        
        if not node_details:
            return jsonify({"error": "Invalid node"}), 400
        
        # Generate image URL with dynamic seed and enhanced prompt
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        path_tuples = [(node, game_state.get("sentiment_tally", {}).get(node, 0)) 
                       for node in path_node_ids]
        
        base_prompt = node_details.get("prompt", "")
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create the image URL
        encoded_prompt = requests.utils.quote(enhanced_prompt)
        image_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}"
        
        # Personalize choices with variations except the first choice
        choices = node_details.get("choices", [])
        if choices and len(choices) > 0:
            # Keep a deep copy to avoid modifying the original
            choices = [choice.copy() for choice in choices]
            
            # Get user's personality traits from sessions or generate new ones
            if session_id not in user_sessions:
                user_sessions[session_id] = {}
            
            if 'personality_traits' not in user_sessions[session_id]:
                # Generate random personality traits for this user
                import random
                traits = ["cautious", "bold", "diplomatic", "direct", "curious", "practical", 
                          "optimistic", "pessimistic", "detailed", "concise"]
                user_sessions[session_id]['personality_traits'] = random.sample(traits, 3)
            
            user_traits = user_sessions[session_id]['personality_traits']
            
            # Get a hash from the session ID to make choices consistently unique per user
            session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
            
            # Personalize choices (except first one at the start node) with small variations
            for i, choice in enumerate(choices):
                # Skip first choice at start node to keep it consistent
                if current_node_id == "start" and i == 0:
                    continue
                    
                original_text = choice.get("text", "")
                
                # Adjective modifiers based on personality
                adjectives = {
                    "cautious": ["carefully", "cautiously", "deliberately"],
                    "bold": ["boldly", "bravely", "confidently"],
                    "diplomatic": ["politely", "respectfully", "graciously"],
                    "direct": ["directly", "straightforwardly", "bluntly"],
                    "curious": ["curiously", "inquisitively", "wonderingly"],
                    "practical": ["practically", "sensibly", "reasonably"],
                    "optimistic": ["hopefully", "optimistically", "eagerly"],
                    "pessimistic": ["warily", "skeptically", "doubtfully"],
                    "detailed": ["meticulously", "thoroughly", "carefully"],
                    "concise": ["simply", "briefly", "efficiently"]
                }
                
                # Get suitable adjectives for this user's personality
                suitable_adjectives = []
                for trait in user_traits:
                    if trait in adjectives:
                        suitable_adjectives.extend(adjectives[trait])
                
                if suitable_adjectives:
                    # Select a consistent adjective based on session and choice
                    adj_index = (session_hash + i) % len(suitable_adjectives)
                    selected_adj = suitable_adjectives[adj_index]
                    
                    # Insert the adjective into the choice text if it makes sense
                    # Identify the verb in the choice text
                    words = original_text.split()
                    # Simple heuristic: Look for verbs typical in choices
                    common_verbs = ["Take", "Go", "Explore", "Talk", "Help", "Ignore", "Follow", "Leave", 
                                   "Examine", "Search", "Ask", "Fight", "Run", "Hide", "Climb", "Jump"]
                    
                    for j, word in enumerate(words):
                        if word in common_verbs and j < len(words) - 1:
                            # Insert adjective after the verb
                            modified_text = " ".join(words[:j+1]) + " " + selected_adj + " " + " ".join(words[j+1:])
                            choice["text"] = modified_text
                            break
        
        # Get the score from the game state, ensuring consistency in property names
        score = game_state.get("score", 0)
        
        # Prepare the response
        response_data = {
            "situation": node_details.get("situation", ""),
            "translation": node_details.get("translation", ""),
            "is_end": node_details.get("is_end", False),
            "ending_category": node_details.get("ending_category", ""),
            "choices": choices,  # Use personalized choices
            "image_url": image_url,
            "image_prompt": enhanced_prompt,
            "current_score": score,  # Use consistent name for frontend
            "score": score,  # Include both for backward compatibility
            "vocabulary_words": node_details.get("vocabulary_words", [])
        }
        
        # Generate special end-game content if this is an end node
        if node_details.get("is_end", False):
            manga_prompt = f"Manga style, story summary of {enhanced_prompt}"
            encoded_manga_prompt = requests.utils.quote(manga_prompt)
            response_data["manga_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}"
            
            summary_prompt = f"Fantasy book cover, hero's journey, {enhanced_prompt}"
            encoded_summary_prompt = requests.utils.quote(summary_prompt)
            response_data["summary_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_summary_prompt}"
        
        # Create response with cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('session_id', session_id, max_age=86400*30)  # 30 days
        return response
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/choice', methods=['POST'])
def make_choice():
    try:
        data = request.json
        choice_index = data.get('choice_index')
        
        if choice_index is None:
            return jsonify({"error": "Missing choice_index"}), 400
        
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        current_node_id = game_state["current_node_id"]
        
        # Get current node details
        language = data.get('language', 'es')
        node_details = get_node_details(current_node_id, language)
        if not node_details:
            return jsonify({"error": "Invalid current node"}), 400
            
        # Validate choice index
        if not node_details.get("choices") or choice_index >= len(node_details["choices"]):
            return jsonify({"error": "Invalid choice index"}), 400
            
        # Get the chosen choice
        choice = node_details["choices"][choice_index]
        
        # Special processing for dynamic ending calculation
        next_node_id = choice.get("next_node")
        if next_node_id == "_calculate_end":
            # Calculate ending based on score and sentiment
            score = game_state.get("score", 0)
            sentiment_tally = game_state.get("sentiment_tally", {})
            
            # Count positive vs negative tags
            positive_count = sum(sentiment_tally.get(tag, 0) for tag in 
                             ["kind", "adventurous", "bold", "wise", "resourceful"])
            negative_count = sum(sentiment_tally.get(tag, 0) for tag in 
                             ["selfish", "cautious", "stubborn"])
            
            # Determine ending based on score and sentiment balance
            if score >= 8 and positive_count > negative_count:
                next_node_id = "language_expert_ending"
            elif score >= 4:
                next_node_id = "language_learner_ending"
            else:
                next_node_id = "language_beginner_ending"
                
            # Create a unique ending variation based on the session ID
            # This ensures each user gets a different ending
            custom_endings = {
                "language_expert_ending": [
                    "language_expert_ending", "vocabulary_master_ending", "polyglot_ending"
                ],
                "language_learner_ending": [
                    "language_learner_ending", "word_collector_ending", "language_explorer_ending"
                ],
                "language_beginner_ending": [
                    "language_beginner_ending", "first_steps_ending", "language_starter_ending"
                ]
            }
            
            if next_node_id in custom_endings:
                # Use the session ID to pick a specific variant
                session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
                ending_options = custom_endings[next_node_id]
                ending_index = session_hash % len(ending_options)
                custom_ending = ending_options[ending_index]
                
                # If we have this ending defined, use it instead
                if custom_ending in story_nodes:
                    next_node_id = custom_ending
        
        # Update game state
        game_state["current_node_id"] = next_node_id
        game_state["path_history"].append(next_node_id)
        
        # Update score
        score_modifier = choice.get("score_modifier", 0)
        game_state["score"] += score_modifier
        
        # Update sentiment tally
        tag = choice.get("tag")
        if tag:
            if tag not in game_state["sentiment_tally"]:
                game_state["sentiment_tally"][tag] = 0
            game_state["sentiment_tally"][tag] += 1
        
        # Record this choice
        game_state["choice_history"].append({
            "from_node": current_node_id,
            "choice_index": choice_index,
            "choice_text": choice.get("text", ""),
            "tag": tag
        })
        
        # Save the updated state
        user_sessions[session_id]['state'] = game_state
        
        # Return the new state
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_game():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            session_id = hashlib.md5(f"{time.time()}-{os.urandom(8).hex()}".encode()).hexdigest()
        
        # Reset the game state for this session
        reset_game_state(session_id)
        
        # Instead of just returning success message, return the actual game state
        # by calling the get_current_state function
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/share-image', methods=['GET'])
def generate_share_image():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        
        # Get score and ending information
        score = game_state.get("score", 0)
        current_node_id = game_state.get("current_node_id", "")
        node_details = get_node_details(current_node_id)
        
        if not node_details:
            return jsonify({"error": "Invalid node"}), 400
            
        # Check if the game has ended
        if not node_details.get("is_end", False):
            return jsonify({"error": "Game has not ended yet"}), 400
            
        # Get the ending category
        ending_category = node_details.get("ending_category", "Adventure Complete")
        
        # Generate the specific manga image prompt with user's journey details
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        
        # Generate main traits from sentiment tally
        main_traits = []
        for tag, count in sentiment_tally.items():
            if count > 0:
                main_traits.append(tag)
        
        # Select top 3 traits if we have that many
        top_traits = main_traits[:3] if len(main_traits) >= 3 else main_traits
        traits_text = ", ".join(top_traits)
        
        # Create a personalized story description
        personality = f"a {traits_text} adventurer" if traits_text else "an adventurer"
        
        # Generate image URL with enhanced prompt
        base_prompt = node_details.get("prompt", "")
        path_tuples = [(node, sentiment_tally.get(node, 0)) for node in path_node_ids]
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        # Get dynamic seed
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        # Generate enhanced prompt for manga-style image
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create manga-style panel layout prompt
        share_manga_prompt = f"Manga style, 4-panel comic strip telling the story of {personality} who achieved the '{ending_category}' ending with a score of {score}, {enhanced_prompt}, clean white background with title 'Mystic Forest Adventure' and score displayed"
        
        # URL encode the prompt
        encoded_manga_prompt = requests.utils.quote(share_manga_prompt)
        share_image_url = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}"
        
        # Return the share image URL
        return jsonify({
            "share_image_url": share_image_url,
            "score": score,
            "ending_category": ending_category
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Vercel expects the app object for Python runtimes
# The file is usually named index.py inside an 'api' folder
# If running locally:
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')