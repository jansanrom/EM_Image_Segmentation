import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (ELU, UpSampling3D, Add, Dense, Activation, Reshape, Flatten, Permute, Dropout, 
                                     Lambda, SpatialDropout3D, Conv3D, Conv3DTranspose, MaxPooling3D, concatenate, 
                                     BatchNormalization)
from tensorflow.keras.regularizers import l2
from engine.metrics import binary_crossentropy_weighted, jaccard_index, jaccard_index_softmax


def U_Net_3D_Xiao(image_shape, lr=0.0001, n_classes=2):
    """Create 3D U-Net.

       Parameters
       ----------
       image_shape : array of 3 int
           Dimensions of the input image.
        
       activation : str, optional
           Keras available activation type.

       lr : float, optional
           Learning rate value.

       n_classes : int, optional
           Number of classes.
    
       Returns  
       -------
       model : Keras model
           Xiao 3D U-Net type proposed network model.


       Here is a picture of the network extracted from the original paper:

       .. image:: ../../img/xiao_network.jpg                                               
           :width: 100%                                                         
           :align: center  
    """

    dinamic_dim = (None,)*(len(image_shape)-1) + (1,)
    inputs = Input(dinamic_dim)
        
    x = Conv3D(3, (3, 3, 3), activation=None,
               kernel_initializer='he_normal', padding='same')(inputs)
    x = BatchNormalization()(x)
    x = ELU() (x)

    # Encoder
    s1 = residual_block(x, 32)
    x = MaxPooling3D((2, 2, 1), padding='same') (s1)
    s2 = residual_block(x, 48)
    x = MaxPooling3D((2, 2, 1), padding='same') (s2)
    s3 = residual_block(x, 64)
    x = MaxPooling3D((2, 2, 1), padding='same') (s3)
    x = residual_block(x, 80) 
   
    # Decoder 
    x = UpSampling3D((2, 2, 1)) (x)
    x = Conv3D(64, (1, 1, 1), activation=None, kernel_initializer='he_normal', 
               padding='same')(x)
    x = BatchNormalization()(x)
    x = ELU() (x)
    x = Add()([s3, x])

    x = residual_block(x, 64)
    x = UpSampling3D((2, 2, 1)) (x)
        
    # Auxiliary ouput 1 
    a1 = UpSampling3D((2, 2, 1)) (x)    
    a1 = Conv3D(n_classes, (1, 1, 1), activation=None,
                kernel_initializer='he_normal', padding='same',
                kernel_regularizer=l2(0.01), name='aux1')(a1)
    a1 = Activation('softmax')(a1)


    x = Conv3D(48, (1, 1, 1), activation=None, kernel_initializer='he_normal', 
               padding='same')(x)
    x = BatchNormalization()(x)
    x = ELU() (x)
    x = Add()([s2, x])

    x = residual_block(x, 48)
    x = UpSampling3D((2, 2, 1)) (x)
    x = Conv3D(32, (1, 1, 1), activation=None, kernel_initializer='he_normal', 
               padding='same')(x)
    x = BatchNormalization()(x)
    x = ELU() (x)

    # Auxiliary ouput 2
    a2 = Conv3D(n_classes, (1, 1, 1), activation=None,
                kernel_initializer='he_normal', padding='same',
                kernel_regularizer=l2(0.01), name='aux2')(x)
    a2 = Activation('softmax')(a2)


    x = Add()([s1, x])
    x = residual_block(x, 32)
    x = Conv3D(3, (3, 3, 3), activation=None, kernel_initializer='he_normal', 
               padding='same', kernel_regularizer=l2(0.01))(x)
    x = BatchNormalization()(x)
    x = ELU() (x)

    # Adapt the output to use softmax pixel-wise 
    x = Conv3D(n_classes, (1, 1, 1), activation=None, 
               kernel_initializer='he_normal', padding='same')(x)
    outputs = Activation('softmax', name='main_classifier')(x)
   
    model = Model(inputs=[inputs], outputs=[a1, a2, outputs])
    
    opt = tf.keras.optimizers.Adam(lr=lr, beta_1=0.9, beta_2=0.999, 
                                   epsilon=1e-8, decay=0.0, amsgrad=False)
        
    model.compile(optimizer=opt, loss="categorical_crossentropy", 
                  loss_weights=[0.15, 0.3, 1], metrics=[jaccard_index_softmax])

    return model

def residual_block(inp_layer, channels):
    """Residual block definition.   

       Parameters
       ----------
       inp_layer : Keras layer
           Input layer. 

       channels : int
           Number of feature maps to use in Conv layers.

       Returns
       -------
       out : Keras layer
           Last layer of the block. 
    """
    a = Conv3D(channels, (1, 1, 1), activation=None,
           kernel_initializer='he_normal', padding='same')(inp_layer)
    a = BatchNormalization()(a)
    a = ELU() (a)

    b = Conv3D(channels, (3, 3, 3), activation=None,
               kernel_initializer='he_normal', padding='same')(inp_layer)
    b = BatchNormalization()(b)
    b = ELU() (b)
    b = Conv3D(channels, (3, 3, 3), activation=None,
               kernel_initializer='he_normal', padding='same')(b)
    b = BatchNormalization()(b)
    b = ELU() (b)

    return Add()([a, b])
