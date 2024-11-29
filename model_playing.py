import time
import numpy as np
from main import BrickBreakerEnv
import tensorflow as tf

# Load the model
model = tf.keras.models.load_model('brick_breaker_dqn.h5')

# Initialize the environment
env = BrickBreakerEnv()

# Reset the environment to start a new game
state = env.reset()

done = False
total_reward = 0

try:
    while not done:
        # Render the environment
        env.render()

        # Model predicts the next action
        action = np.argmax(model.predict(state[np.newaxis]))

        # Step the environment with the predicted action
        state, reward, done, info = env.step(action)
        total_reward += reward

        # Small delay for smoother playback
        time.sleep(0.02)

    print(f"Game Over! Final Score: {info['score']}, Time Elapsed: {info['time']:.2f}s")

finally:
    env.close()
