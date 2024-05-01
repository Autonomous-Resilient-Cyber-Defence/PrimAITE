import yaml
from stable_baselines3 import PPO
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.vec_env import SubprocVecEnv

from primaite.session.environment import PrimaiteGymEnv

EPISODE_LEN = 128
NUM_EPISODES = 10
NO_STEPS = EPISODE_LEN * NUM_EPISODES
BATCH_SIZE = 32
LEARNING_RATE = 3e-4

with open("c:/projects/primaite/src/primaite/config/_package_data/data_manipulation.yaml", "r") as f:
    cfg = yaml.safe_load(f)


def make_env(rank: int, seed: int = 0) -> callable:
    """Wrapper script for _init function."""

    def _init() -> PrimaiteGymEnv:
        env = PrimaiteGymEnv(env_config=cfg)
        env.reset(seed=seed + rank)
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=LEARNING_RATE,
            n_steps=NO_STEPS,
            batch_size=BATCH_SIZE,
            verbose=0,
            tensorboard_log="./PPO_UC2/",
        )
        model.learn(total_timesteps=NO_STEPS)
        return env

    set_random_seed(seed)
    return _init


if __name__ == "__main__":
    n_procs = 4
    train_env = SubprocVecEnv([make_env(i + n_procs) for i in range(n_procs)])
