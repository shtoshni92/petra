import torch

from controller.controller import Controller
from gap_utils.gap import GAPDataset


class Inference:
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        checkpoint = torch.load(model_path, map_location=self.device)
        self.model = Controller(**checkpoint['model_args']).to(self.device)
        self.model.load_state_dict(checkpoint['model'], strict=False)
        self.model.eval()  # Eval mode

        self.tokenizer = GAPDataset.load_bert_tokenizer()

    def batchify_input_text(self, doc):
        """Given an input sentence, batchify it for input.
        doc: Document string
        """
        doc = "[CLS] " + doc + " [SEP]"
        text = self.tokenizer.tokenize(doc)
        text_length = len(text)

        return text, text_length

    def perform_inference(self, doc):
        text, text_length = self.batchify_input_text(doc)

        # Convert to tensor and pass
        text_length_tens = torch.tensor([len(text)]).to(self.device)
        text_ids = self.tokenizer.convert_tokens_to_ids(text)
        text_tens = torch.unsqueeze(torch.tensor(text_ids), dim=0).to(self.device)

        # Get output from model
        outputs, _ = self.model.get_model_outputs(text_tens, text_length_tens)
        coref, overwrite, ent, usage =\
            (outputs['coref'], outputs['overwrite'], outputs['ent'], outputs['usage'])

        output_dict = {
            'text': text,
            'coref': [coref[j][0].tolist() for j in range(text_length)],
            'overwrite': [overwrite[j][0].tolist() for j in range(text_length)],
            'usage': [usage[j][0].tolist() for j in range(text_length)],
            'ent': ['{:.3f}'.format(ent[j][0].item()) for j in range(text_length)],
        }
        return output_dict
