"""
Class for a generic trainer used for training all the different generative models
"""
from models import cvae_gan
from models.attention import *
from torch.utils.data import DataLoader, Dataset
import os
from skimage import io, transform
import scipy.misc as m
from torchvision import transforms


USE_CUDA = torch.cuda.is_available()


class StatesDataset(Dataset):
    """

    Dataset consisting of the frames of the Atari Game-
    Montezuma Revenge

    """

    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.images = []
        self.list_files()

    def __len__(self):
        return len(self.images)

    def list_files(self):
        for m in os.listdir(self.root_dir):
            if m.endswith('.jpg'):
                self.images.append(m)

    def __getitem__(self, idx):
        m = self.images[idx]
        image = io.imread(os.path.join( self.root_dir, m))
        sample = {'image': image}

        if self.transform:
            sample = self.transform(sample)

        return sample

# Transformations
class Rescale(object):
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or int): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        self.output_size = output_size

    def __call__(self, sample):
        image = sample['image']

        h, w = image.shape[:2]
        if isinstance(self.output_size, int):
            if h > w:
                new_h, new_w = self.output_size, self.output_size
            else:
                new_h, new_w = self.output_size, self.output_size * w / h
        else:
            new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)

        img = transform.resize(image, (new_h, new_w))

        return {'image': img}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        image = sample['image']

        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))

        return {'image': torch.FloatTensor(torch.from_numpy(image).float())}


if __name__ == '__main__':
    image_size = 96
    seed = 100
    input_images = 'montezuma_resources'

    dataset = StatesDataset(root_dir=input_images, transform=
        transforms.Compose([Rescale(image_size), ToTensor()]))

    encoder = cvae_gan.Encoder(conv_layers=32, conv_kernel_size=3, latent_space_dim=64,
                               hidden_dim=128, use_cuda=USE_CUDA, height=96, width=96,
                               input_channels=3, pool_kernel_size=2)
    generator = cvae_gan.Generator(conv_layers=32, conv_kernel_size=2, latent_space_dimension=64,
                                   height=96, width=96, hidden_dim=128, input_channels=3)
    discriminator = cvae_gan.Discriminator(input_channels=3, conv_layers=32, conv_kernel_size=3, pool_kernel_size=2,
                                           hidden=128, height=96, width=96)

    if USE_CUDA:
        generator = generator.cuda()
        discriminator = discriminator.cuda()
        encoder = encoder.cuda()



    cvae_gan = cvae_gan.CVAEGAN(encoder=encoder, batch_size=8, num_epochs=100,
                                random_seed=seed, dataset=dataset, discriminator=discriminator,
                                generator=generator, discriminator_lr=0.00005, encoder_lr=0.00005,
                                generator_lr=0.00005, use_cuda=USE_CUDA, output_folder='cvae_gan_output/')

    cvae_gan.train(lambda_1=3, lambda_2=1)

