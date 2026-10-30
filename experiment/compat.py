"""Make the paper repo and the AWQ model load under transformers 5 on CUDA 13.

Import this before loading the model or calling the repo's ConversationEncoder.
"""

from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from transformers.utils import quantization_config as qc

# gptqmodel's Marlin kernels fail to JIT-compile on CUDA 13; the pure-torch AWQ kernel
# uses the same weights.
_awq_post_init = qc.AwqConfig.post_init


def _post_init(self):
    """Force the pure-torch AWQ backend, then run the original AwqConfig.post_init."""
    self.backend = qc.AwqBackend.TORCH_AWQ
    _awq_post_init(self)


qc.AwqConfig.post_init = _post_init

# transformers 5 returns an Encoding from apply_chat_template(tokenize=True); the repo
# expects the v4 list of ids.
_apply_chat_template = PreTrainedTokenizerBase.apply_chat_template


def _apply_chat_template_v4(self, *args, **kwargs):
    """apply_chat_template that returns a plain list of ids (v4 behaviour) unless told otherwise."""
    kwargs.setdefault("return_dict", False)
    return _apply_chat_template(self, *args, **kwargs)


PreTrainedTokenizerBase.apply_chat_template = _apply_chat_template_v4
