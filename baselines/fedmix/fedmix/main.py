import hydra
from hydra.utils import instantiate
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf
import flwr as fl

from fedmix.dataset import load_datasets
from fedmix import client, server
from fedmix.utils import save_results_as_pickle

@hydra.main(config_path="conf", config_name="cifar10", version_base=None)
def main(cfg):
    print(OmegaConf.to_yaml(cfg))

    seed = cfg.seed
    device = cfg.device
    num_gpus = cfg.num_gpus
    num_clients = cfg.num_clients
    clients_per_round = cfg.clients_per_round
    num_rounds = cfg.num_rounds

    dataset_config = cfg.dataset
    model_config = cfg.model
    strategy_config = cfg.strategy
    client_config = cfg.client

    trainloaders, testloader, mashed_data = load_datasets(
        dataset_config, num_clients, seed)

    client_fn = client.gen_client_fn(client_config, trainloaders, model_config)
    evaluate_fn = server.gen_evaluate_fn(testloader, device, model_config)

    strategy = instantiate(
        strategy_config, mashed_data=mashed_data, evaluate_fn=evaluate_fn)

    history = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=num_clients,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        client_resources={'num_gpus': num_gpus},
        strategy=strategy
    )

    print('----------------------')
    print(history)
    print('----------------------')

    save_path = HydraConfig.get().runtime.output_dir
    save_results_as_pickle(history, file_path=save_path, extra_results={})


if __name__ == "__main__":
    main()
